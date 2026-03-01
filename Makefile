setup-db:
	psql "postgresql://github:github@localhost:5433/github_analytics" -f sql/schema.sql
	psql "postgresql://github:github@localhost:5433/github_analytics" -f sql/views.sql

ingest:
	python src/ingest.py microsoft apple netflix google anthropic openai meta github

all: setup-db ingest