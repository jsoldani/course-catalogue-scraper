import argparse
import asyncio
import re
from pathlib import Path

from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

# ============================================================
# CONFIGURATION
# ============================================================

START_URL = (
    "https://unipi.coursecatalogue.cineca.it/"
    "corsi/2025/11527?codicione=0500106203100002"
)

OUTPUT_DIR = Path("course_pdfs")
LOG_FILE = OUTPUT_DIR / "download_errors.log"

HEADLESS = True
MAX_DEPTH = 10

FRACTION_PATTERN = re.compile(
    r"^\s*Vedi dettaglio\s*$",
    re.IGNORECASE
)

# ============================================================
# UTILITY FUNCTIONS
# ============================================================


def safe_filename(value):
    """Produce a filesystem-safe filename."""

    value = re.sub(r'[\\/:*?"<>|]', "_", value)
    value = re.sub(r"\s+", "_", value.strip())

    return value[:150] or "corso"


def unique_path(directory, filename):
    """Never overwrite an existing PDF."""

    path = directory / filename
    counter = 1

    while path.exists():
        path = directory / (
            f"{Path(filename).stem}_{counter}.pdf"
        )
        counter += 1

    return path


def log_error(course, reason, fraction=None):
    """Write failed operations to the log file."""

    fraction_info = (
        f"Frazione: {fraction}"
        if fraction is not None
        else "Frazione: principale"
    )

    message = (
        f"Codice: {course['code']} | "
        f"Insegnamento: {course['text']} | "
        f"{fraction_info} | "
        f"Errore: {reason}"
    )

    print(f"[LOG ERROR] {message}")

    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(message + "\n")


def fraction_name(path):
    """Convert a hierarchical fraction path into a string."""

    return ".".join(str(i) for i in path) or "principale"


# ============================================================
# CLICKABLE ELEMENTS
# ============================================================


async def get_fraction_buttons(page):
    """
    Find all clickable elements whose text is exactly
    'Vedi dettaglio', preserving their DOM order.
    """

    elements = page.locator(
        "a, button, [role='button']"
    )

    indices = await elements.evaluate_all(
        """elements => elements
            .map((element, index) => ({
                index,
                text: (
                    element.innerText ||
                    element.getAttribute('aria-label') ||
                    ''
                ).trim()
            }))
            .filter(item =>
                /^Vedi dettaglio$/i.test(item.text)
            )
            .map(item => item.index)
        """
    )

    return [
        elements.nth(index)
        for index in indices
    ]


async def find_clickable(page, label):
    """Find a link or button by its exact visible text."""

    pattern = re.compile(
        rf"^\s*{re.escape(label)}\s*$",
        re.IGNORECASE
    )

    for role in ("link", "button"):
        locator = page.get_by_role(
            role,
            name=pattern
        )

        if await locator.count() > 0:
            return locator.first

    locator = page.get_by_text(pattern)

    if await locator.count() > 0:
        return locator.first

    return None


async def click_fraction(context, page, index):
    """
    Actually click the index-th 'Vedi dettaglio' element.

    Supports both same-tab navigation and popup/new-tab navigation.
    """

    buttons = await get_fraction_buttons(page)

    if index < 1 or index > len(buttons):
        raise RuntimeError(
            f"Frazione {index} non disponibile "
            f"(trovate {len(buttons)} frazioni)"
        )

    button = buttons[index - 1]

    previous_pages = set(context.pages)

    print(
        f"    [CLICK] Vedi dettaglio #{index}"
    )

    await button.click(timeout=15000)

    # Allow navigation or popup creation.
    await page.wait_for_timeout(1000)

    new_pages = [
        p for p in context.pages
        if p not in previous_pages
    ]

    if new_pages:
        destination = new_pages[-1]

        try:
            await destination.wait_for_load_state(
                "domcontentloaded",
                timeout=30000
            )
        except PlaywrightTimeoutError:
            pass

        await destination.wait_for_timeout(1000)

        return destination

    # Same-tab navigation or dynamic page update.
    try:
        await page.wait_for_load_state(
            "domcontentloaded",
            timeout=5000
        )
    except PlaywrightTimeoutError:
        pass

    await page.wait_for_timeout(1000)

    return page


# ============================================================
# NAVIGATION: REPLAY A FRACTION PATH
# ============================================================


async def open_fraction_path(context, course, path):
    """
    Open the original course page and replay all clicks
    needed to reach a specific fraction.

    Example:
        path = (2, 1)

    Means:
        1. Click the second 'Vedi dettaglio'.
        2. Inside that page, click the first 'Vedi dettaglio'.

    Replaying the clicks allows us to handle nested fractions
    even when the website uses JavaScript navigation.
    """

    page = await context.new_page()

    try:
        await page.goto(
            course["url"],
            wait_until="domcontentloaded",
            timeout=60000
        )

        await page.wait_for_timeout(1200)

        for index in path:

            destination = await click_fraction(
                context,
                page,
                index
            )

            # If a new tab was opened, close the previous one.
            if destination is not page:
                await page.close()
                page = destination

        return page

    except Exception:
        if not page.is_closed():
            await page.close()
        raise


# ============================================================
# PDF DOWNLOAD
# ============================================================


async def save_pdf(page, course, path):
    """
    Click 'Salva PDF' and save the generated download.

    The filename reflects the complete hierarchical
    fraction path.
    """

    button = await find_clickable(
        page,
        "Salva PDF"
    )

    fraction = fraction_name(path)

    if button is None:

        log_error(
            course,
            "Bottone 'Salva PDF' non trovato",
            fraction
        )

        return False

    if path:
        filename = safe_filename(
            f"{course['code']}_frazione_{'_'.join(map(str, path))}"
        ) + ".pdf"
    else:
        filename = safe_filename(
            course["code"]
        ) + ".pdf"

    destination = unique_path(
        OUTPUT_DIR,
        filename
    )

    try:

        async with page.expect_download(
            timeout=45000
        ) as info:

            await button.click(timeout=15000)

        download = await info.value

        await download.save_as(
            str(destination)
        )

        print(
            f"    [OK] PDF salvato: {destination.name}"
        )

        return True

    except PlaywrightTimeoutError:

        log_error(
            course,
            "Timeout: download PDF non rilevato",
            fraction
        )

        return False

    except Exception as e:

        log_error(
            course,
            f"Errore durante il download: {e}",
            fraction
        )

        return False


# ============================================================
# RECURSIVE FRACTION PROCESSING
# ============================================================


async def process_node(
    context,
    course,
    path=()
):
    """
    Recursively explore the fraction tree.

    A page is considered a leaf only when it contains
    no further 'Vedi dettaglio' buttons.

    PDFs are downloaded only from leaf pages.
    """

    current_fraction = fraction_name(path)

    print(
        f"\n  [VISITA] {course['code']} "
        f"/ {current_fraction}"
    )

    if len(path) > MAX_DEPTH:

        log_error(
            course,
            f"Profondità massima ({MAX_DEPTH}) superata",
            current_fraction
        )

        return 0

    page = None
    successful_downloads = 0

    try:

        # Open the requested node by replaying its click path.
        page = await open_fraction_path(
            context,
            course,
            path
        )

        print(
            f"    [PAGINA] {page.url}"
        )

        # Find further fractions.
        buttons = await get_fraction_buttons(page)

        fraction_count = len(buttons)

        if fraction_count == 0:

            # LEAF NODE: no further fractions.
            print(
                "    [FOGLIA] Nessun ulteriore dettaglio"
            )

            result = await save_pdf(
                page,
                course,
                path
            )

            return 1 if result else 0

        # INTERNAL NODE: recursively explore all children.
        print(
            f"    [RAMIFICAZIONE] "
            f"{fraction_count} frazioni trovate"
        )

        # Store the number of children before navigation.
        for index in range(
            1,
            fraction_count + 1
        ):

            child_path = path + (index,)

            print(
                f"\n    [FIGLIO] "
                f"{fraction_name(child_path)}"
            )

            successful_downloads += await process_node(
                context,
                course,
                child_path
            )

        return successful_downloads

    except Exception as e:

        log_error(
            course,
            f"Errore durante la navigazione: {e}",
            current_fraction
        )

        return successful_downloads

    finally:

        if page is not None and not page.is_closed():
            await page.close()


# ============================================================
# COURSE PROCESSING
# ============================================================


async def process_course(context, course):

    print(
        f"\n{'=' * 65}\n"
        f"[INSEGNAMENTO] {course['text']}\n"
        f"{'=' * 65}"
    )

    successful = await process_node(
        context,
        course,
        path=()
    )

    print(
        f"\n[RISULTATO] {course['code']}: "
        f"{successful} PDF scaricati"
    )

    return successful


# ============================================================
# MAIN
# ============================================================

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Scarica i PDF degli insegnamenti dal Course Catalogue."
    )

    parser.add_argument(
        "--start-url",
        default=START_URL,
        help="URL della pagina iniziale del corso."
    )

    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Directory in cui salvare i PDF."
    )

    return parser.parse_args()

async def main():
    global START_URL, OUTPUT_DIR

    args = parse_arguments()

    START_URL = args.start_url
    OUTPUT_DIR = Path(args.output_dir)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Reset the error log for this execution.
    LOG_FILE.write_text(
        "LOG DOWNLOAD PDF - ERRORI\n"
        "==========================\n\n",
        encoding="utf-8"
    )

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=HEADLESS
        )

        context = await browser.new_context(
            accept_downloads=True
        )

        page = await context.new_page()

        # ----------------------------------------------------
        # STEP 1: Open degree programme page.
        # ----------------------------------------------------

        print(
            "[APERTURA] Pagina del corso di laurea"
        )

        await page.goto(
            START_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        await page.wait_for_timeout(2000)

        # ----------------------------------------------------
        # STEP 2: Click 'Insegnamenti offerti'.
        # ----------------------------------------------------

        print(
            "[NAVIGAZIONE] Insegnamenti offerti"
        )

        offered_button = await find_clickable(
            page,
            "Insegnamenti offerti"
        )

        if offered_button is None:

            print(
                "[ERRORE] Bottone 'Insegnamenti offerti' "
                "non trovato"
            )

            await browser.close()
            return

        await offered_button.click()

        await page.wait_for_timeout(2500)

        # ----------------------------------------------------
        # STEP 3: Wait for course list.
        # ----------------------------------------------------

        try:

            await page.wait_for_function(
                """() => Array.from(
                    document.querySelectorAll('a[href]')
                ).some(a =>
                    /^\\s*\\[[^\\]]+\\]/.test(
                        a.innerText.trim()
                    )
                )""",
                timeout=30000
            )

        except PlaywrightTimeoutError:

            print(
                "[ATTENZIONE] Elenco degli insegnamenti "
                "non individuato"
            )

        # ----------------------------------------------------
        # STEP 4: Collect offered courses.
        # ----------------------------------------------------

        links = await page.locator(
            "a[href]"
        ).evaluate_all(
            """anchors => anchors.map(a => ({
                href: a.href,
                text: a.innerText.trim()
            }))"""
        )

        courses = {}

        for link in links:

            match = re.match(
                r"^\s*\[([^\]]+)\]",
                link["text"]
            )

            if match:

                code = match.group(1).strip()

                courses[link["href"]] = {
                    "code": code,
                    "text": link["text"],
                    "url": link["href"]
                }

        courses = list(
            courses.values()
        )

        await page.close()

        print(
            f"\nInsegnamenti individuati: "
            f"{len(courses)}"
        )

        # ----------------------------------------------------
        # STEP 5: Process every course recursively.
        # ----------------------------------------------------

        total_downloads = 0

        for index, course in enumerate(
            courses,
            start=1
        ):

            print(
                f"\n\n{'#' * 65}\n"
                f"INSEGNAMENTO {index}/{len(courses)}\n"
                f"{course['text']}\n"
                f"{'#' * 65}"
            )

            total_downloads += await process_course(
                context,
                course
            )

        await browser.close()

    # --------------------------------------------------------
    # STEP 6: Final report.
    # --------------------------------------------------------

    pdf_count = len(
        list(OUTPUT_DIR.glob("*.pdf"))
    )

    print(
        "\n" + "=" * 65
    )

    print(
        "DOWNLOAD COMPLETATO"
    )

    print(
        f"Insegnamenti individuati: {len(courses)}"
    )

    print(
        f"PDF scaricati in questa esecuzione: "
        f"{total_downloads}"
    )

    print(
        f"PDF presenti nella cartella: {pdf_count}"
    )

    print(
        f"Log errori: {LOG_FILE.resolve()}"
    )

    print(
        f"Cartella: {OUTPUT_DIR.resolve()}"
    )

    print(
        "=" * 65
    )


if __name__ == "__main__":
    asyncio.run(main())
