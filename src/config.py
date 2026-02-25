import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DB_URL = os.getenv("DB_URL")
BASE_URL = "https://api.github.com"

if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN is not set")

if not DB_URL:
    raise ValueError("DB_URL is not set")