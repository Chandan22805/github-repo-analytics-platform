import sys
from datetime import date

from github_client import GitHubClient
from db import get_connection, bulk_insert_repos, bulk_insert_companies, bulk_insert_snapshots, get_last_run, update_last_run

def run_ingestion(username:str):
    conn = get_connection()
    
    try:
        client = GitHubClient()
        last_run = get_last_run(conn, username)
        repos = client.get_user_repos(username, since=last_run)
        companies = {}
        repos_to_insert = {}
        snapshots = []
    
        for repo in repos :
            
            company_id = repo["owner"]["id"]
            company_name = repo["owner"]["login"]
            
            companies[company_id] = company_name
            
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
        
        bulk_insert_companies(conn, companies)
        print("Inserted companies")
        
        bulk_insert_repos(conn, repos_to_insert)
        print("Inserted repos")
        
        bulk_insert_snapshots(conn, snapshots)
        print("Inserted snapshots")
        
        update_last_run(conn, username, date.today())
        conn.commit()
            
    finally:
        conn.close()
         
if __name__ == "__main__":
    companies = sys.argv[1:]
    for company in companies :
        run_ingestion(company)