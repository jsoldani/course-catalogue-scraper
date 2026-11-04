# Course Catalogue Scraper

Questa repository contiene alcuni script Python per scaricare automaticamente i documenti PDF associati agli insegnamenti pubblicati sul [Course Catalogue dell'Università di Pisa](https://unipi.coursecatalogue.cineca.it/).

## Contenuto della repository

La repository include i seguenti script:

- **`scrape_one.py`**: scarica tutti i documenti PDF disponibili per un singolo CdS. Lo script naviga il Course Catalogue partendo dalla pagina relativa al CdS scelto, esplora ricorsivamente le eventuali sezioni e frazioni annidate (seguendo i collegamenti *Vedi dettaglio*) e scarica i relativi PDF.
- **`scrape_all.py`**: esegue `scrape_one.py` per una lista predefinita di CdS, salvando i documenti scaricati in directory separate.

Durante l'esecuzione, `scrape_one.py` genera inoltre un file `download_errors.log`, che contiene informazioni sugli insegnamenti o sulle frazioni per cui, eventualmente, il download non è andato a buon fine.

## Requisiti

Gli script richiedono Python 3 e la libreria [Playwright](https://playwright.dev/python/).

Installare Playwright con il comando:

```bash
pip install playwright
```

Installare i browser necessari:

```bash
playwright install chromium
```

## Utilizzo

### Scaricare i documenti di un singolo CdS

Per scaricare i PDF associati a un singolo CdS, eseguire:

```bash
python3 scrape_one.py --start-url "<URL_CDS_COURSE_CATALOGUE>" --output-dir "<DIRECTORY_DESTINAZIONE>"
```

I due parametri da riga di comando sono:

- `--start-url`: URL della pagina del CdS sul Course Catalogue dell'Università di Pisa.
- `--output-dir`: directory in cui salvare i PDF scaricati. Se non esiste, viene creata automaticamente.

Ad esempio:

```bash
python3 scrape_one.py \
    --start-url "https://unipi.coursecatalogue.cineca.it/corsi/2025/11527" \
    --output-dir "INFR-L"
```

### Scaricare i documenti di più CdS

Per scaricare i PDF di tutti gli CdS elencati in `scrape_all.py`, eseguire:

```bash
python3 scrape_all.py
```

Lo script esegue sequenzialmente `scrape_one.py` per ciascun insegnamento definito nel dizionario `COURSES`. I PDF vengono salvati in una directory dedicata, il cui nome corrisponde al codice del CdS (specificato come chiave del dizionario).

## Configurazione dei CdS da scaricare

La lista dei CdS elaborati da `scrape_all.py` è definita nel dizionario `COURSES`, all'inizio del file:

```python
COURSES = {
    "INFR-L": "https://unipi.coursecatalogue.cineca.it/corsi/2025/11527",
    "WIF-LM": "https://unipi.coursecatalogue.cineca.it/corsi/2025/10436",
    "WDB-LM": "https://unipi.coursecatalogue.cineca.it/corsi/2025/11357",
    "WDH-LM": "https://unipi.coursecatalogue.cineca.it/corsi/2025/11434"
}
```

**Per scaricare altri CdS o edizioni relative ad anni accademici differenti, è necessario aggiornare questo dizionario.**

In particolare:

- Per aggiungere un CdS, inserire una nuova voce utilizzando il codice del CdS come chiave e il corrispondente URL del Course Catalogue come valore.
- Per scaricare una diversa edizione di un CdS già presente, modificare il relativo URL in modo che punti alla pagina dell'edizione desiderata.
- Per escludere un CdS dallo scraping, rimuovere la relativa voce dal dizionario.

Ad esempio, per aggiungere un nuovo insegnamento:

```python
COURSES = {
    "INFR-L": "https://unipi.coursecatalogue.cineca.it/corsi/2025/11527",
    "NEW-COURSE": "https://unipi.coursecatalogue.cineca.it/corsi/2025/XXXXX"
}
```

**Attenzione:** non tutti gli insegnamenti sono necessariamente disponibili sul Course Catalogue per ogni anno accademico. Ad esempio, per WTW-LM non è presente una voce relativa all'anno accademico 2025/2026.

## Output

Al termine dell'esecuzione, la directory della repository conterrà una cartella per ciascun insegnamento elaborato, ad esempio:

```text
.
├── scrape_one.py
├── scrape_all.py
├── README.md
├── INFR-L/
│   ├── <codice-insegnamento>.pdf
│   ├── <codice-insegnamento>_frazione_1.pdf
│   └── ...
├── WIF-LM/
│   └── ...
├── WDB-LM/
│   └── ...
└── WDH-LM/
    └── ...
```

I nomi dei file PDF identificano l'insegnamento e, quando necessario, la frazione da cui è stato scaricato il documento, comprese le eventuali frazioni annidate.

Il file `download_errors.log`, generato da `scrape_one.py` nella directory di lavoro corrente, riporta eventuali errori di navigazione o download.