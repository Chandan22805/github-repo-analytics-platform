import pytest
from unittest.mock import MagicMock

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