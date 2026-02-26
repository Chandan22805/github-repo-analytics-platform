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

    def get_user_repos(self, username: str):
        """List repos for authenticated user"""
        url = f"{BASE_URL}/users/{username}/repos"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()