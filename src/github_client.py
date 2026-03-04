import time
import requests
from config import GITHUB_TOKEN, BASE_URL

class GitHubClient:

    def __init__(self):
        
        if not GITHUB_TOKEN:
            raise ValueError("GitHub token not found in environment variables")

        self.headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }
        
        print("GitHub Client initialized successfully")

    def get_user_repos(self, username: str, since=None, retries: int = 3):
        """List repos for authenticated user"""
        all_repos = []
        page = 1
        
        while True:
        
            url = f"{BASE_URL}/users/{username}/repos"
            params = {
                "per_page" : 100,
                "page" : page
            } 
            if since:
                params["since"] = since.isoformat()
               
            for attempt in range(retries):
                
                try:
                    response = requests.get(url, 
                                            headers=self.headers,
                                            params=params)
                    
                    # Rate limit handling
                    remaining = int(response.headers.get("X-RateLimit-Remaining", 1))
                    reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                    
                    if remaining == 0:
                        sleep_seconds = max(reset_time - int(time.time()), 0)
                        time.sleep(sleep_seconds)
                        continue
                        
                    response.raise_for_status()
                    repos = response.json()
                    break  
                
                except requests.exceptions.HTTPError as e:
                    status = e.response.status_code
                    
                    if(status >= 500 and attempt < retries -1 ):
                        wait_time = 2 ** attempt
                        time.sleep(wait_time)
                        continue
                    
                    else:
                        raise
                
                except requests.exceptions.RequestException:
                    
                    if attempt < retries - 1:
                        wait_time = 2 ** attempt
                        time.sleep(wait_time)
                        continue
                    else:
                        raise
            
            if not repos:
                break
            
            all_repos.extend(repos)
            page += 1
            
        return all_repos    
    
    def get_repo_languages(self, owner:str, repo:str , retries :int = 3):
        
        url = f"{BASE_URL}/repos/{owner}/{repo}/languages"
        languages = None    
        
        if not owner or not repo:
            raise ValueError("Owner and repo parameters required")
        
        for attempt in range(retries):
            
            try:
                response = requests.get(url, 
                                        headers=self.headers,
                                        )
                
                # Rate limit handling
                remaining = int(response.headers.get("X-RateLimit-Remaining", 1))
                reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                
                if remaining == 0:
                    sleep_seconds = max(reset_time - int(time.time()), 0)
                    time.sleep(sleep_seconds)
                    continue
                    
                response.raise_for_status()
                languages = response.json()
                break  
            
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code
                
                if(status >= 500 and attempt < retries -1 ):
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                
                else:
                    raise
            
            except requests.exceptions.RequestException:
                
                if attempt < retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                else:
                    raise
        
        return languages