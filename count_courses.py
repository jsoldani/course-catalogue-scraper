
#!/usr/bin/env python3

import argparse
from pathlib import Path


# Stringhe che, se presenti nel nome di un PDF, ne comportano l'esclusione.
EXCLUDED_CODES = [
    # INFR-L
    "002ZY",  # CONOSCENZA DELLA LINGUA INGLESE
    "1895Z",  # PROVA FINALE
    "1896Z",  # TIROCINIO
    "212ZW",  # LIBERA SCELTA PER RICONOSCIMENTI
    "717ZW",  # LIBERA SCELTA PER RICONOSCIMENTI
    "605ZW",  # SCELTA 2
    "INF01",  # TEST DI VALUTAZIONE DI INFORMATICA

    # WDB-LM
    "1619Z",  # THESIS

    # WDH-LM
    "2200Z",  # FINAL THESIS

    # WIF-LM
    "927ZW",  # THESIS
]


def is_excluded(pdf_path):
    """Verifica se il nome del PDF contiene uno dei codici esclusi."""
    filename = pdf_path.name

    return any(
        excluded_code in filename
        for excluded_code in EXCLUDED_CODES
    )


def get_course_code(pdf_path):
    """
    Restituisce il codice dell'insegnamento, ottenuto dal prefisso
    del nome del file che precede il primo underscore.
    """
    return pdf_path.stem.split("_", 1)[0]


def main():
    parser = argparse.ArgumentParser(
        description="Conta gli insegnamenti distinti presenti in una cartella."
    )

    parser.add_argument(
        "folder",
        help="Cartella contenente i PDF da analizzare."
    )

    args = parser.parse_args()

    folder_path = Path(args.folder)

    if not folder_path.is_dir():
        parser.error(f"La cartella '{folder_path}' non esiste.")

    # Individuazione dei PDF ed esclusione di quelli specificati.
    all_pdf_files = sorted(
        pdf
        for pdf in folder_path.rglob("*")
        if pdf.is_file()
        and pdf.suffix.lower() == ".pdf"
    )

    excluded_files = [
        pdf for pdf in all_pdf_files if is_excluded(pdf)
    ]

    pdf_files = [
        pdf for pdf in all_pdf_files if not is_excluded(pdf)
    ]

    # Estrazione dei codici distinti degli insegnamenti.
    course_codes = sorted({
        get_course_code(pdf)
        for pdf in pdf_files
    })

    # Risultati.
    print(f"PDF individuati: {len(all_pdf_files)}")
    print(f"PDF esclusi: {len(excluded_files)}")
    print(f"PDF considerati: {len(pdf_files)}")
    print(f"\nNumero di insegnamenti distinti: {len(course_codes)}")

    print("\nCodici degli insegnamenti:")
    for code in course_codes:
        print(f"  - {code}")


if __name__ == "__main__":
    main()
