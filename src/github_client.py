import requests
from config import GITHUB_TOKEN, BASE_URL

class GitHubClient:

    def __init__(self):
        
        if not self.token:
            raise ValueError("GitHub token not found in environment variables")

        self.headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }

    def get_user(self):
        """Get authenticated user info"""
        url = f"{BASE_URL}/user"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_repo(self, owner: str, repo: str):
        """Get repository details"""
        url = f"{BASE_URL}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def list_user_repos(self):
        """List repos for authenticated user"""
        url = f"{BASE_URL}/user/repos"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()