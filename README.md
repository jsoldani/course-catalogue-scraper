# Course Catalogue Scraper

Questa repository contiene alcuni script Python per scaricare automaticamente i documenti PDF associati agli insegnamenti pubblicati sul [Course Catalogue dell'Università di Pisa](https://unipi.coursecatalogue.cineca.it/).

## Contenuto della repository

La repository include i seguenti script:

- **`scrape_one.py`**: scarica tutti i documenti PDF disponibili per un singolo CdS. Lo script naviga il Course Catalogue partendo dalla pagina relativa al CdS scelto, esplora ricorsivamente le eventuali sezioni e frazioni annidate (seguendo i collegamenti *Vedi dettaglio*) e scarica i relativi PDF.
- **`scrape_all.py`**: esegue `scrape_one.py` per una lista predefinita di CdS, salvando i documenti scaricati in directory separate.
- **`check_pdfs.py`** consente di verificare automaticamente la presenza di una serie di campi obbligatori nei PDF degli insegnamenti scaricati dal Course Catalogue.

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

## Verifica dei PDF degli insegnamenti (`check_pdfs.py`)

Lo script `check_pdfs.py` consente di verificare automaticamente la presenza di una serie di campi obbligatori nei PDF degli insegnamenti scaricati dal Course Catalogue.

Lo script analizza ricorsivamente tutti i PDF presenti nella cartella specificata, incluse le eventuali sottocartelle, ed estrae il testo per verificare la presenza delle frasi richieste.

### Requisiti

Lo script utilizza la libreria Python `pypdf`, che può essere installata con:

```bash
pip install pypdf
```

### Utilizzo

Lo script richiede come unico argomento il percorso della cartella contenente i PDF da analizzare:

```bash
python3 check_pdfs.py <cartella>
```

Ad esempio:

```bash
python3 check_pdfs.py INFR-L
```

L'analisi comprende tutti i file con estensione `.pdf` presenti nella cartella indicata e nelle sue sottocartelle.

### Funzionamento

Per ciascun PDF, lo script:

1. Estrae il testo da tutte le pagine del documento.
2. Normalizza il testo per rendere il confronto indipendente da maiuscole/minuscole, spazi e interruzioni di riga.
3. Verifica la presenza di tutte le frasi obbligatorie definite nella lista `REQUIRED_PHRASES` all'interno dello script.
4. Individua, quando presente, la prima riga contenente un codice alfanumerico racchiuso tra parentesi quadre (ad esempio `[12345]`).
5. Registra le eventuali frasi mancanti.

Alcuni PDF possono essere esclusi automaticamente dall'analisi: i codici identificativi da escludere sono definiti nella lista `EXCLUDED_CODES` all'interno dello script. Un PDF viene escluso quando il suo nome contiene uno dei codici presenti nella lista.

### Report prodotti

Al termine dell'analisi vengono generati quattro report direttamente nella cartella specificata come argomento.

| File | Descrizione |
|---|---|
| `_check_results.txt` | Report dettagliato dei PDF nei quali manca almeno una frase obbligatoria. Per ciascun documento riporta il nome del file, la riga contenente il codice identificativo (oppure un'indicazione se il codice non è stato trovato) e l'elenco delle frasi mancanti. Include inoltre una sezione dedicata ai PDF che non è stato possibile analizzare. |
| `_check_results_short.csv` | Riepilogo sintetico delle verifiche. Per ciascuna frase riporta il numero di PDF in cui è assente e la lista dei relativi nomi (senza estensione). Il file è generato con codifica UTF-8 con BOM per facilitarne l'apertura con strumenti come Microsoft Excel. |
| `_check_all_missing.txt` | Elenco dei soli PDF nei quali mancano tutte le frasi obbligatorie. Per ciascun documento riporta il nome del file e la riga contenente il codice identificativo (oppure un'indicazione se il codice non è stato trovato). |
| `_check_results_report.txt` | Report compatto che riporta il numero totale di PDF con almeno una frase mancante e, per ciascuna frase obbligatoria, la lista dei codici dei corsi in cui essa è assente, senza ripetizioni, insieme al numero di codici distinti. Il codice del corso è ricavato dal prefisso del nome del PDF che precede il primo carattere `_`. |

I PDF che non possono essere analizzati, ad esempio a causa di errori di lettura, vengono segnalati esclusivamente nel report dettagliato e non sono inclusi nel report `_check_all_missing.txt` né nei conteggi delle frasi mancanti, poiché non è possibile stabilire se contengano o meno i campi richiesti.

### Personalizzazione

È possibile modificare il comportamento dello script intervenendo sulle due liste definite all'inizio del file:

- `REQUIRED_PHRASES`: contiene le frasi che devono essere presenti nei PDF. Per aggiungere o rimuovere un controllo è sufficiente modificare questa lista.
- `EXCLUDED_CODES`: contiene i codici identificativi dei PDF da escludere dall'analisi.

In questo modo, lo script può essere facilmente riutilizzato per verificare documenti relativi a corsi di studio differenti o ad anni accademici successivi.

È possibile modificare il comportamento dello script intervenendo sulle due liste definite all'inizio del file:

- `REQUIRED_PHRASES`: contiene le frasi che devono essere presenti nei PDF. Per