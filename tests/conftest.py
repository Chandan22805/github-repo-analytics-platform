import pytest
from unittest.mock import MagicMock
import os

os.environ.setdefault("GITHUB_TOKEN", "test-token")
os.environ.setdefault("DB_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("AWS_BUCKET_NAME", "test-bucket")

@pytest.fixture
def mock_conn():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn

@pytest.fixture
def mock_github_client():
    client = MagicMock()
    client.get_user_repos.return_value = []
    client.get_repo_languages.return_value = {}
    return client