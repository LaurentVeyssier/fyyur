# Project Fyyur

## Project description

this is the final project of UDACITY first course from ["backend developper with python"](https://www.udacity.com/course/backend-developer-with-python--nd0044) 5-course nanodegree.

It is a musical booking web application for artists and venues, built with Flask and powered by a PostgreSQL database backend. The app provides a full-stack experience, with Flask handling routing and server-side logic, Jinja templates rendering dynamic HTML pages, and PostgreSQL storing all artist, venue, and show data. It is running locally.

I've included instructions below to set up the database with initial data and run the app.

Initial requirements:
- python 3.12
- postgresql
- uv

## initial setup

from the project root folder, run:

```bash
uv init
uv venv
uv add requirements.txt
```

## DB creation and migration

### DB creation

login to psql using : psql -h localhost -U postgres
in psql, created local postgres BD fyyur using : CREATE DATABASE fyyur; 

(to delete the db, use DROP DATABASE fyyur;)

### DB initialization

in powershell: (MAKE SURE TO RUN from your virtual env to detect flask)

```bash
flask db init        # first time only
flask db migrate -m "Initial migration"
flask db upgrade
```
this instantiated the tables Venue, Artist and Show in the DB as per model definitions in app.py
check schema in psql using 
```bash
\c fyyur     # connect to the db
\d "Artist"; # check schema
```

### DB set-up

run populate_DB_init.py. This will populate the existing DB with initial data.

check in psql using 

```bash
SELECT * FROM "Venue";
SELECT * FROM "Artist";
SELECT * FROM "Show";
```

## App launch

create a .env file and add your db path:

```bash
DATABASE_URL = your_db_path
```

then run:

```bash
uv run python app.py
```





## Notes: if needed, to reset auto increment (modify the table name)

in psql console:

```sql
WITH reordered AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS new_id
    FROM "Venue"
)
UPDATE "Venue" v
SET id = r.new_id
FROM reordered r
WHERE v.id = r.id;
```

 \d "Venue"

```sql
 SELECT setval('"Venue_id_seq"', (SELECT MAX(id) FROM "Venue"));
 # check: select * from "Artist";
 ```
