import sys
import logging
from datetime import date

from github_client import GitHubClient
from db import get_connection, bulk_insert_companies, bulk_insert_repos, bulk_insert_snapshots, get_last_run, update_last_run, get_latest_repo_metrics, get_all_companies

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/ingestion.log")
    ]
)

logger = logging.getLogger(__name__)

def run_ingestion(username=None):
    conn = get_connection()
    logger.info("Starting ingestion")
    try:
        client = GitHubClient()
        repos_to_insert = {}
        snapshots = []
        companies_to_insert = {}
        changed_repo_ids = set()
        today = date.today()
        
        companies = ( [username] if username else get_all_companies(conn) )
        logger.info(f"Companies to process: {len(companies)}")
        
        for company in companies:
            last_run = get_last_run(conn, company)
            repos = client.get_user_repos(company, since=last_run)
            
            for repo in repos :
                
                company_id = repo["owner"]["id"]
                company_name = repo["owner"]["login"]
                
                companies_to_insert[company_id] = company_name
                
                repos_to_insert[repo["id"]] = (
                    repo["id"],
                    company_id,
                    repo["name"],
                    repo["full_name"],
                    repo["language"],
                    repo["created_at"],
                    repo["updated_at"],
                )
                
                snapshots.append((
                    repo["id"],
                    date.today(),
                    repo["stargazers_count"],
                    repo["forks_count"],
                    repo["open_issues_count"]
                ))
                
                changed_repo_ids.add(repo["id"])
                
            update_last_run(conn, company, date.today())
        
        latest_metrics = get_latest_repo_metrics(conn)
        
        for repo_id, metrics in latest_metrics.items():
            if repo_id not in changed_repo_ids:
                stars, forks, open_issues = metrics
                
                snapshots.append((
                    repo_id,
                    today,
                    stars,
                    forks,
                    open_issues
                ))
        
        logger.info(f"Total companies to insert: {len(companies_to_insert)}")
        bulk_insert_companies(conn, companies_to_insert)
        
        logger.info(f"Total repos to insert: {len(repos_to_insert)}")
        bulk_insert_repos(conn, repos_to_insert)
        
        logger.info(f"Total snapshots to insert: {len(snapshots)}")
        bulk_insert_snapshots(conn, snapshots)
        
        logger.info("Committing transaction")
        conn.commit()
            
    finally:
        conn.close()
        logger.info("Ingestion completed successfully")
         
if __name__ == "__main__":
    companies = sys.argv[1:]
    for company in companies :
        run_ingestion(company)