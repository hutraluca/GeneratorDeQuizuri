# Quiz Generator

Aplicatie CLI (Command Line Interface) pentru generarea si rularea de quiz-uri educationale.
Permite testarea cunostintelor folosind intrebari din fisier, cu suport pentru scor, timer, feedback si statistici.

## Autor
- **Nume:** Hut Raluca-Stefania
- **Grupă:** 2.1
- **Email:** raluca-stefania.hut@student.upt.ro
- **An academic:** 2025-2026

## Descriere
Quiz Generator este o aplicatie de tip CLI (Command Line Interface) destinata generarii
si rularii de quiz-uri eduactionale. Aplicatia permite incarcarea intrebarilor din fisier
JSON, configurarea modului de rulare si salvarea rezultatelor pentru analiza ulterioara.

Aplicatia este utila pentru autoevaluare si testare, fiind potrivita pentru scenarii
educationale unde este necesara o evaluare rapida fara interfata grafica.

## Tehnologii folosite
- **Limbaj:** Python 3.12
- **Biblioteci:**
    - argparse - parsarea argumentelor din linia de comanda
    - json - citirea si salvarea datelor
    - random - randomizarea intrebarilor si optiunilor
    - time, datetime - masurarea timpului
    - pathlib - manipularea fisierelor
- **Tools:** Git, Docker, GitHub

## Cerințe sistem
- Python 3.10+
- Sistem de operare: Windows/Linux/macOS
- Docker (optional, pentru rulare in container)

## Instalare
```bash
## Clone repository
git clone https://github.com/hutraluca/GeneratorDeQuizuri
cd quiz_gen

## Nu sunt necesare dependente externe 

## Rulare

## Comandă de bază
py quiz_gen.py --help

# Exemple de comenzi
py quiz_gen.py --num 10 --timed 20 --mode exam --feedback immediate --user Ion
py quiz_gen.py --category matematica --num 5
py quiz_gen.py --mode practice --feedback final
py quiz_gen.py --stats --user Ion
py quiz_gen.py --add_question --interactive --file questions.json

# Exemple de utilizare
Exemplul 1: Quiz examen cu timer
py quiz_gen.py --num 5 --timed 20 --mode exam
Exemplul 2: Quiz practica
py quiz_gen.py --mode practice
Exemplul 3: Filtrare pe categorie
py quiz_gen.py --category geografie --num 5
Exemplul 4: Statistici utilizator
py quiz_gen.py --stats --user Ion
Exemplul 5: Adaugare intrebare
py quiz_gen.py --add_question --interactive

Funcționalități implementate
[x] Intrebari multiple choice
[x] Intrebari true/false
[x] Intrebari short answer
[x] Citire intrebari din fisier JSON
[x] Randomizaare intrebari si optiuni
[x] Timer per intrebare
[x] Sistem de punctaj cu penalizari
[x] Mod practica (fara scor)
[x] Mod examen (cu scor)
[x] Feedback imediat sau la final
[x] Salvare rezultate sesiuni
[x] Salvare progresului utilizatorului
[x] Generare de statistici
[x] Categorii de intrebari
[x] Adaugare intrebari interactiv din terminal

Structura proiectului
quiz_gen/
├── quiz_gen.py - logica principala a aplicatiei
├── questions.json - baza de intrebari
├── README.md - documentatie
└── results/
  ├── results_*.json -rezultate salvate
  └── progress.json - progres utilizator

Decizie de design
Intrebarile sunt stocate in format JSON pentru flexibilitate si extensibilitate.
Aplicatia este rulata din linia de comanda pentru simplitate si portabilitate.
Salvarea progresului previne repetarea intrebarilor si imbunatateste experienta utilizatorului.

Probleme întâlnite și soluții
Problema: Repetarea acelorasi intrebari
Solutie: Salvarea ID-urilor intrebarilor recente in progress.json
Problema: Gestionarea timerului fara blocarea programului
Solutie: Masurarea timpului de raspuns cu time.time()

Testare
Testarea s-a realizat manual prin rularea aplicatiei cu diverse combinatii
de argumente si verificarea output-ului si a fiserelor rezultate.

Docker
# Build imagine
docker build -t quiz_gen .
# Rulare container
docker run -it --rm quiz_gen --num 5 --mode exam --timed 20 --feedback immediate --user Ion

Resurse folosite

# Youtube - Tutoriale video
- Create a Quiz Game with Python – https://www.youtube.com/watch?v=zehwgTB0vV8
- Build a Quiz Application in Python – https://www.youtube.com/watch?v=kqa-BYI46ss
- Quiz Game Using Data From a JSON File (Python) – https://www.youtube.com/watch?v=V4hOC8RWpjU
- Building a Multiple Choice Quiz | Python Tutorial – https://www.youtube.com/watch?v=SgQhwtIoQ7o

#Articole si tutoriale
- Build a Quiz Application With Python (Real Python) – https://realpython.com/python-quiz-application/

Contact
Pentru întrebări: raluca-stefania.hut@student.upt.ro