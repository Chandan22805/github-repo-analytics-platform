import sys
import logging
import time
from datetime import date

from github_client import GitHubClient
from db import get_connection, get_latest_repo_metrics, get_latest_language_metrics, get_all_companies, get_all_languages, get_last_run,\
               bulk_insert_companies, bulk_insert_repos, bulk_insert_languages, bulk_insert_snapshots, bulk_insert_language_snapshots,\
               update_last_run, clean_up_db
from archive import export_to_s3

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_ingestion(usernames=None):
    start_time = time.time()
    conn = get_connection()
    logger.info("Starting Phase-I of ingestion pipeline")
    try:
        client = GitHubClient()
        repos_to_insert = {}
        repo_snapshots = []
        language_snapshots_raw = []
        language_snapshots = []
        companies_to_insert = {}
        languages_to_insert = set()
        changed_repo_ids = set()
        today = date.today()
        last_run = get_last_run(conn)
        latest_repo_metrics = get_latest_repo_metrics(conn)
        latest_language_metrics = get_latest_language_metrics(conn)
        companies = usernames if usernames else get_all_companies(conn) 
        logger.info(f"Companies to process: {len(companies)}")

    finally:
        conn.close()
        logger.info("Phase-I completed : Database fetch completed successfully")
    
    logger.info("Starting Phase-II of ingestion pipeline")
    
    conn = None
    
    try:
        for company in companies:
            
            repos = client.get_user_repos(company, since=last_run.get(company))
            
            if len(repos) == 0:
                logger.warning(f"No repos returned for {company}")
                
            if not isinstance(repos, list):
                logger.error("Unexpected GitHub API response format")
            for repo in repos :
                # print(repo["name"])
                if not repo.get("id"):
                    logger.warning("Repo missing ID. Skipping.")
                    continue
                
                if not repo.get("owner"):
                    logger.warning("Repo missing owner. Skipping.")
                    continue
                
                company_id = repo["owner"]["id"]
                company_name = repo["owner"]["login"]
                companies_to_insert[company_id] = company_name
                repo_name = repo["name"]
                
                repos_to_insert[repo["id"]] = (
                    repo["id"],
                    company_id,
                    repo_name,
                    repo["full_name"],
                    repo["language"],
                    repo["created_at"],
                    repo["updated_at"],
                )
                
                repo_snapshots.append((
                    repo["id"],
                    today,
                    repo["stargazers_count"],
                    repo["forks_count"],
                    repo["open_issues_count"]
                ))
                
                languages = client.get_repo_languages(company_name, repo_name)
                
                if not languages:
                    logger.warning(f"No languages detected for repo {repo_name}")
                else:
                    for language_name, bytes_ in languages.items():
                        languages_to_insert.add(language_name)

                        language_snapshots_raw.append((
                            repo["id"],
                            today,
                            language_name,
                            bytes_
                        ))
                    
                changed_repo_ids.add(repo["id"])
        
        conn = get_connection()
        update_last_run(conn, {company : today for company in companies})
        
        for repo_id, metrics in latest_repo_metrics.items():
            if repo_id not in changed_repo_ids:
                stars, forks, open_issues = metrics
                
                repo_snapshots.append((
                    repo_id,
                    today,
                    stars,
                    forks,
                    open_issues
                ))
        
        for repo_id, lang_dict in latest_language_metrics.items():
            if repo_id not in changed_repo_ids:
                for language_id, bytes_ in lang_dict.items():
                    language_snapshots.append((
                        repo_id,
                        today,
                        language_id,
                        bytes_
                    )) 
                
        logger.info(f"Total companies to insert: {len(companies_to_insert)}")
        bulk_insert_companies(conn, companies_to_insert)
        
        logger.info(f"Total repos to insert: {len(repos_to_insert)}")
        bulk_insert_repos(conn, repos_to_insert)
        
        logger.info(f"Total languages to insert: {len(languages_to_insert)}")
        bulk_insert_languages(conn, languages_to_insert)
        
        language_mapping = get_all_languages(conn)
        
        for repo_id, snapshot_date, language_name, bytes_ in language_snapshots_raw:
            language_snapshots.append((
                repo_id, 
                snapshot_date, 
                language_mapping[language_name],
                bytes_
            ))
        
        logger.info(f"Total snapshots to insert: {len(repo_snapshots)}")
        bulk_insert_snapshots(conn, repo_snapshots)
        
        logger.info(f"Total language snapshots to insert: {len(language_snapshots)}")
        bulk_insert_language_snapshots(conn, language_snapshots)
        
        if len(repo_snapshots) < 5:
            logger.warning("Unusually low snapshot count detected")    
        
        clean_up_db(conn)
        
        export_to_s3()
        
        logger.info("Committing transaction")
        conn.commit()
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(
            f"""
            Pipeline run summary
            --------------------
            Companies processed: {len(companies)}
            Repos updated: {len(changed_repo_ids)}
            Repo snapshots written: {len(repo_snapshots)}
            Language snapshots written: {len(language_snapshots)}
            New languages discovered: {len(languages_to_insert)}
            Duration: {duration:.2f} seconds
            """
            )
        
    finally:
        if conn:
            conn.close()
        logger.info("Phase-II completed : Ingestion completed successfully")
         
if __name__ == "__main__":
    companies = sys.argv[1:]
    if companies:
        run_ingestion(companies)
    else:
        run_ingestion()