connect-db: 
	podman start pg-github

setup-db:
	psql "postgresql://github:github@localhost:5433/github_analytics" -f sql/schema.sql
	psql "postgresql://github:github@localhost:5433/github_analytics" -f sql/views.sql

ingest:
	python src/ingest.py 
	
all: 
	connect-db 
	setup-db 
	ingest