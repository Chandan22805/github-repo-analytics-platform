from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.abspath("src"))
from ingest import run_ingestion

def test_ingestion_with_empty_companies_list(mock_conn, mock_github_client):
    with patch("ingest.GitHubClient") as MockClient:
        MockClient.return_value = mock_github_client
        with patch("ingest.get_all_companies", return_value=[]):
            with patch("ingest.get_connection", return_value=mock_conn):
                with patch("db.execute_values"):
                    run_ingestion()
                    mock_conn.commit.assert_called_once()