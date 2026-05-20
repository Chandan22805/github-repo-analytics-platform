connect-db: 
	podman start pg-github

setup-db:
	psql "REMOVED" -f sql/schema.sql
	psql "REMOVED" -f sql/views.sql

ingest:
	python src/ingest.py 
	
all: 
	connect-db 
	setup-db 
	ingest