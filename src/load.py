import logging

from db import (
    bulk_insert_companies,
    bulk_insert_language_snapshots,
    bulk_insert_languages,
    bulk_insert_repos,
    bulk_insert_snapshots,
    get_all_languages,
    update_last_run
)

logger = logging.getLogger(__name__)

def load(conn, batch, extra_repo_snapshots, extra_language_snapshots):

    language_mapping = get_all_languages(conn)

    for repo_id, snapshot_date, language_name, bytes_ in batch.language_snapshots_raw:
        batch.language_snapshots.append((
            repo_id,
            snapshot_date,
            language_mapping[language_name],
            bytes_
        ))

    repo_snapshots = batch.repo_snapshots + extra_repo_snapshots
    language_snapshots = batch.language_snapshots + extra_language_snapshots 
    
    logger.info(f"Updating last run")
    update_last_run(conn,batch.last_run)

    logger.info(f"Total companies to insert: {len(batch.companies_to_insert)}")
    bulk_insert_companies(conn, batch.companies_to_insert)
    
    logger.info(f"Total repos to insert: {len(batch.repos_to_insert)}")
    bulk_insert_repos(conn, batch.repos_to_insert)
    
    logger.info(f"Total languages to insert: {len(batch.languages)}")
    bulk_insert_languages(conn, batch.languages)

    logger.info(f"Total snapshots to insert: {len(repo_snapshots)}")
    bulk_insert_snapshots(conn, repo_snapshots)
    
    logger.info(f"Total language snapshots to insert: {len(language_snapshots)}")
    bulk_insert_language_snapshots(conn, language_snapshots)