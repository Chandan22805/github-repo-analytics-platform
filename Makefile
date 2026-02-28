setup-db:
	psql -f sql/schema.sql
	psql -f sql/views.sql

ingest:
	python src/ingest.py $(cat companies.txt)

all: setup-db ingest