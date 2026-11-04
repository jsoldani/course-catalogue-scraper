import subprocess

COURSES = {
    "INFR-L": "https://unipi.coursecatalogue.cineca.it/corsi/2025/11527",
    "WIF-LM": "https://unipi.coursecatalogue.cineca.it/corsi/2025/10436",
    "WDB-LM": "https://unipi.coursecatalogue.cineca.it/corsi/2025/11357",
    "WDH-LM": "https://unipi.coursecatalogue.cineca.it/corsi/2025/11434"
}
## ATTENZIONE: per WTW-LM non c'è una entry per a.a. 2025/2026 su Course Catalogue

def main(): 
    for course in COURSES:
        print("*****************************")
        print(" SCRAPING: " + course)
        print("*****************************")
        url = COURSES[course]
        command = "python3 scrape_one.py --start-url '" + url + "' --output-dir '" + course + "'"
        subprocess.run(command)

if __name__ == "__main__":
    main()
