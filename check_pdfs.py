#!/usr/bin/env python3

import argparse
import csv
import re
import unicodedata
from pathlib import Path

from pypdf import PdfReader


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


REQUIRED_PHRASES = [
    "Obiettivi di apprendimento",
    "Modalità di verifica delle conoscenze",
    "Capacità",
    "Modalità di verifica delle capacità",
    "Metodi didattici",
    "Modalità di verifica dei comportamenti",
    "Prerequisiti",
    "Co-requisites",
    "Indicazioni metodologiche",
    "Contenuti",
    "Bibliografia e materiale didattico",
    "Indicazioni per non frequentanti",
    "Obiettivi Agenda 2030 per lo sviluppo sostenibile"
]


def normalize_text(text):
    """Normalizza il testo per rendere il confronto più robusto."""
    text = unicodedata.normalize("NFKC", text)
    text = text.casefold()
    return " ".join(text.split())


def extract_pdf_text(pdf_path):
    """Estrae il testo da tutte le pagine di un PDF."""
    reader = PdfReader(str(pdf_path))

    return "\n".join(
        page.extract_text() or ""
        for page in reader.pages
    )


def find_course_code_line(text):
    """
    Restituisce la prima riga contenente un codice alfanumerico
    racchiuso tra parentesi quadre, oppure None se non trovato.
    """
    pattern = re.compile(r"\[[A-Za-z0-9]+\]")

    for line in text.splitlines():
        if pattern.search(line):
            return line.strip()

    return None


def check_pdf(pdf_path):
    """
    Restituisce le frasi mancanti e la riga contenente
    il codice alfanumerico tra parentesi quadre.
    """
    text = extract_pdf_text(pdf_path)
    normalized_text = normalize_text(text)

    missing_phrases = [
        phrase
        for phrase in REQUIRED_PHRASES
        if normalize_text(phrase) not in normalized_text
    ]

    course_code_line = find_course_code_line(text)

    return missing_phrases, course_code_line


def is_excluded(pdf_path):
    """Verifica se il nome del PDF contiene uno dei codici esclusi."""
    filename = pdf_path.name

    return any(
        excluded_code in filename
        for excluded_code in EXCLUDED_CODES
    )


def get_course_code(pdf_path):
    """
    Restituisce il codice del corso ottenuto dal prefisso
    del nome del file che precede il primo underscore.
    """
    return pdf_path.stem.split("_", 1)[0]


def main():
    parser = argparse.ArgumentParser(
        description="Verifica la presenza di specifiche frasi nei PDF."
    )

    parser.add_argument(
        "folder",
        help="Cartella contenente i PDF da analizzare."
    )

    args = parser.parse_args()

    folder_path = Path(args.folder)

    if not folder_path.is_dir():
        parser.error(f"La cartella '{folder_path}' non esiste.")

    # File di output.
    output_path = folder_path / "_check_results.txt"
    short_output_path = folder_path / "_check_results_short.csv"
    all_missing_output_path = folder_path / "_check_all_missing.txt"
    report_output_path = folder_path / "_check_results_report.txt"

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

    print(f"PDF individuati: {len(all_pdf_files)}")
    print(f"PDF esclusi: {len(excluded_files)}")
    print(f"PDF da analizzare: {len(pdf_files)}")

    if excluded_files:
        print("\nFile esclusi:")
        for pdf in excluded_files:
            print(f"  - {pdf.name}")

    report_lines = []
    all_missing_lines = []
    errors = []
    incomplete_count = 0
    all_missing_count = 0

    # Per ogni frase, memorizza i PDF in cui è assente.
    missing_by_phrase = {
        phrase: [] for phrase in REQUIRED_PHRASES
    }

    # Per ogni frase, memorizza i codici dei corsi in cui è assente.
    # I codici sono mantenuti senza ripetizioni.
    missing_codes_by_phrase = {
        phrase: [] for phrase in REQUIRED_PHRASES
    }

    for index, pdf_path in enumerate(pdf_files, start=1):
        print(f"[{index}/{len(pdf_files)}] Analisi: {pdf_path}")

        try:
            missing_phrases, course_code_line = check_pdf(pdf_path)

            if missing_phrases:
                incomplete_count += 1

                # Codice del corso ricavato dal nome del file.
                course_code = get_course_code(pdf_path)

                # Generazione del report dettagliato.
                report_lines.append(pdf_path.name)

                if course_code_line:
                    report_lines.append(course_code_line)
                else:
                    report_lines.append("[Codice non trovato]")

                report_lines.extend(
                    f"  - {phrase}"
                    for phrase in missing_phrases
                )

                report_lines.append("")

                # Aggiorna i riepiloghi per ciascuna frase mancante.
                for phrase in missing_phrases:
                    missing_by_phrase[phrase].append(
                        pdf_path.stem
                    )

                    if course_code not in missing_codes_by_phrase[phrase]:
                        missing_codes_by_phrase[phrase].append(
                            course_code
                        )

                # Se mancano TUTTE le frasi, aggiunge il PDF
                # al report dedicato.
                if len(missing_phrases) == len(REQUIRED_PHRASES):
                    all_missing_count += 1

                    all_missing_lines.append(pdf_path.name)

                    if course_code_line:
                        all_missing_lines.append(course_code_line)
                    else:
                        all_missing_lines.append("[Codice non trovato]")

                    all_missing_lines.append("")

        except Exception as exc:
            errors.append((pdf_path, str(exc)))

    # Generazione del report dettagliato.
    with output_path.open("w", encoding="utf-8") as output_file:

        if report_lines:
            output_file.write("\n".join(report_lines))
        else:
            output_file.write(
                "Tutti i PDF analizzati contengono le frasi richieste.\n"
            )

        if errors:
            output_file.write("\n\nPDF NON ANALIZZABILI\n")
            output_file.write("===================\n")

            for pdf_path, error in errors:
                relative_path = pdf_path.relative_to(folder_path)
                output_file.write(f"{relative_path}\n")
                output_file.write(f"  Errore: {error}\n\n")

    # Generazione del riepilogo CSV.
    with short_output_path.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:

        writer = csv.writer(csv_file)

        writer.writerow([
            "frase",
            "numero di volte",
            "lista"
        ])

        for phrase in REQUIRED_PHRASES:
            missing_files = missing_by_phrase[phrase]

            writer.writerow([
                phrase,
                len(missing_files),
                "; ".join(missing_files)
            ])

    # Generazione del report dei PDF in cui mancano tutti i campi.
    with all_missing_output_path.open(
        "w",
        encoding="utf-8"
    ) as output_file:

        if all_missing_lines:
            output_file.write("\n".join(all_missing_lines))
        else:
            output_file.write(
                "Nessun PDF presenta tutti i campi mancanti.\n"
            )

    # Generazione del report compatto con i codici dei corsi.
    with report_output_path.open(
        "w",
        encoding="utf-8"
    ) as output_file:

        output_file.write(
            f"PDF con almeno una frase mancante: {incomplete_count}\n\n"
        )

        for phrase in REQUIRED_PHRASES:
            missing_codes = missing_codes_by_phrase[phrase]

            output_file.write(
                f"{phrase} ({len(missing_codes)}): "
                f"{', '.join(missing_codes)}\n"
            )

    print("\nAnalisi completata.")
    print(f"PDF analizzati: {len(pdf_files)}")
    print(f"PDF con frasi mancanti: {incomplete_count}")
    print(f"PDF con tutte le frasi mancanti: {all_missing_count}")
    print(f"PDF non analizzabili: {len(errors)}")
    print(f"Report dettagliato: {output_path}")
    print(f"Report sintetico CSV: {short_output_path}")
    print(f"Report tutti i campi mancanti: {all_missing_output_path}")
    print(f"Report compatto: {report_output_path}")


if __name__ == "__main__":
    main()