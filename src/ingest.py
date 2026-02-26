import sys
from github_client import GitHubClient
from db import insert_repo, insert_company

def run_ingestion(username:str):
    
    client = GitHubClient()

    repos = client.get_user_repos(username)
    
    for repo in repos :
        
        company_data = {
            "id": repo["owner"]["id"],
            "name": repo["owner"]["login"],
        }
        
        repo_data = {
            "id": repo["id"],
            "company_id": repo["owner"]["id"],
            "name": repo["name"],
            "full_name": repo["full_name"],
            "language": repo["language"],
            "stars": repo["stargazers_count"],
            "forks": repo["forks_count"],
            "open_issues": repo["open_issues_count"],
            "created_at": repo["created_at"],
            "updated_at": repo["updated_at"],
        }
    
        insert_company(company_data)
        insert_repo(repo_data)
    
if __name__ == "__main__":
    run_ingestion(sys.argv[1])