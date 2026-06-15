# Secure Wizard

Interaktyvi Flask sistema, kuri anoniminio klausimyno būdu įvertina Windows arba Android įrenginio saugumo būklę ir pateikia individualų veiksmų planą.

## Funkcijos

- Windows ir Android klausimynai.
- Vieno ir kelių atsakymų klausimai.
- Rizikos balas, lygis ir sričių įvertinimas.
- Individualios rekomendacijos pagal atsakymus.
- Anoniminės, riboto galiojimo sesijos.
- JSON API.
- Administratoriaus prisijungimas ir prieigos kontrolė.
- Klausimų, atsakymų ir rekomendacijų CRUD.
- Paieška, filtravimas ir sesijų CSV ataskaita.
- CSRF, įvesties validacija, užklausų ribojimas ir saugumo antraštės.

## Technologijos

- Python 3.11
- Flask 3.1
- SQLAlchemy 2.0 ir SQLite
- Pydantic 2
- Jinja2 ir lokaliai sukompiliuotas Tailwind CSS
- Gunicorn, Nginx, Docker Compose
- pytest ir Ruff

## Nuo ko pradėti

Norint suprasti projektą, pakanka peržiūrėti šiuos failus:

- `app/__init__.py` – aplikacijos sukūrimas ir maršrutų registravimas.
- `app/blueprints/quiz.py` – klausimyno HTTP maršrutai.
- `app/services/quiz_service.py` – klausimyno eiga.
- `app/services/risk_engine.py` – rizikos balo skaičiavimas.
- `app/models/` – duomenų bazės lentelės.
- `app/blueprints/admin.py` – administravimas ir CRUD.
- `tests/` – pagrindinių scenarijų testai.

## Greitas paleidimas su Docker

1. Sukurkite `.env` iš `.env.example`.
2. Sugeneruokite `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

3. Sugeneruokite administratoriaus slaptažodžio maišą:

```bash
docker compose build
docker compose run --rm web flask --app manage admin-hash
```

4. Įrašykite gautą reikšmę į `ADMIN_PASSWORD_HASH` tarp viengubų kabučių:

```dotenv
ADMIN_PASSWORD_HASH='scrypt:...'
```

5. Paleiskite aplikaciją ir paruoškite duomenų bazę:

```bash
docker compose up -d --build
docker compose exec web flask --app manage init-db
docker compose exec web flask --app manage seed
```

Aplikacija bus pasiekiama adresu `http://localhost:8000`.

## Lokalūs kūrimo žingsniai

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
$env:FLASK_ENV = "development"
flask --app manage init-db
flask --app manage seed
flask --app manage run
```

### Linux ir macOS

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
export FLASK_ENV=development
flask --app manage init-db
flask --app manage seed
flask --app manage run
```

## Administravimas

Prisijungimo adresas: `http://localhost:5000/admin/login` lokaliai arba
`http://localhost:8000/admin/login` paleidus su Docker.

Administravimo srityje galima:

- filtruoti ir tvarkyti klausimus;
- kurti, keisti ir šalinti atsakymų variantus;
- filtruoti ir tvarkyti rekomendacijas;
- peržiūrėti sesijų suvestinę;
- eksportuoti ataskaitą CSV formatu.

Pakeitus klausimyno turinį, aktyvios tos platformos anoniminės sesijos panaikinamos, kad seni atsakymai nebūtų maišomi su nauja klausimyno versija.

## API

| Metodas | Kelias | Paskirtis |
|---|---|---|
| `GET` | `/api/v1/platforms` | Platformų sąrašas |
| `POST` | `/api/v1/sessions` | Sukurti sesiją |
| `GET` | `/api/v1/sessions/<token>` | Sesijos būsena |
| `POST` | `/api/v1/sessions/<token>/answer` | Pateikti atsakymą |
| `GET` | `/api/v1/sessions/<token>/result` | Gauti rezultatą |
| `GET` | `/healthz` | Aplikacijos būklė |

## Kokybės patikros

```bash
pytest --cov=app --cov-report=term-missing
ruff check app tests manage.py wsgi.py
```

Projekte yra unit ir integraciniai testai klausimyno eigai, rizikos skaičiavimui, CSRF apsaugai, API ir administravimo prieigos kontrolei.

## Produkcinis diegimas

`docker-compose.prod.yml` prideda Redis bendram užklausų ribojimui, Nginx reverse proxy, TLS konfigūraciją ir periodinį pasenusių sesijų valymą.

Prieš paleidimą:

1. `nginx/nginx.conf` pakeiskite demonstracinį domeną į tikrą.
2. Į `nginx/ssl/` įkelkite `cert.pem` ir `key.pem`.
3. `.env` nustatykite `SECRET_KEY`, `ADMIN_PASSWORD_HASH` ir kitus produkcinius parametrus.
4. Paleiskite:

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec web flask --app manage init-db
docker compose -f docker-compose.prod.yml exec web flask --app manage seed
```

## Projekto struktūra

```text
app/
  blueprints/      HTTP maršrutai
  models/          SQLAlchemy modeliai
  repositories/    duomenų bazės užklausos
  schemas/         Pydantic validacija
  services/        verslo logika
  static/          sukompiliuotas CSS ir JavaScript
  templates/       Jinja2 puslapiai
scripts/           duomenų bazės paruošimo komandos
tests/             unit ir integraciniai testai
nginx/             produkcinio reverse proxy konfigūracija
```
