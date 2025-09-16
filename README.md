# DB creation and migration

## DB creation

login to psql using : psql -h localhost -U postgres
in psql, created local postgres BD fyyur using : CREATE DATABASE fyyur; 

(to delete the db, use DROP DATABASE fyyur;)

## DB initialization

in powershell: (MAKE SURE TO RUN FORM Virutal env to detect flask)

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

## DB POPULATION

run populate_DB_init.py

check in psql using 

```bash
SELECT * FROM "Venue";
SELECT * FROM "Artist";
SELECT * FROM "Show";
```

## App launch

create a .env file and add your db path
DATABASE_URL = your_db_path

```bash
uv run python app.py
```





# Notes
## reset auto increment (modify tablename)

WITH reordered AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS new_id
    FROM "Venue"
)
UPDATE "Venue" v
SET id = r.new_id
FROM reordered r
WHERE v.id = r.id;

 \d "Venue"
 SELECT setval('"Venue_id_seq"', (SELECT MAX(id) FROM "Venue"));
 # check: select * from "Artist";