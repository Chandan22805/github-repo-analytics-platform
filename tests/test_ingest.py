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
                    
def test_ingestion_with_non_empty_companies_list(mock_conn, mock_github_client):
    # Mock GitHub API to return some repos
    mock_github_client.get_user_repos.return_value = [
        {
            "id": 1000,
            "owner": {"id": 12345, "login": "anthropic"},
            "name": "test-repo",
            "full_name": "anthropic/test-repo",
            "language": "Python",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-02",
            "stargazers_count": 100,
            "forks_count": 50,
            "open_issues_count": 10
        }
    ]
    mock_github_client.get_repo_languages.return_value = {"Python": 5000}
    
    with patch("ingest.GitHubClient") as MockClient:
        MockClient.return_value = mock_github_client
        with patch("ingest.get_all_companies", return_value=["anthropic"]):
            with patch("ingest.get_connection", return_value=mock_conn):
                with patch("db.execute_values"):
                    with patch("ingest.get_all_languages", return_value= {"Python" : 1}):
                        run_ingestion()
                        mock_conn.commit.assert_called_once()
                        
def test_ingestion_with_no_repos_for_a_company(mock_conn, mock_github_client, caplog):
    mock_github_client.get_user_repos.return_value = []
    with patch("ingest.GitHubClient") as MockClient:
        MockClient.return_value = mock_github_client
        with patch("ingest.get_all_companies", return_value = ["anthropic"]):
            with patch("ingest.get_connection", return_value= mock_conn):
                with patch("db.execute_values"):
                    run_ingestion()
                    # assert "No repos returned for anthropic" in caplog.text

def test_ingestion_with_improper_format(mock_conn, mock_github_client, caplog):
    mock_github_client.get_user_repos.return_value = [
        {
            "owner": {"id": 12345, "login": "anthropic"},
            "name": "test-repo",
            "full_name": "anthropic/test-repo",
            "language": "Python",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-02",
            "stargazers_count": 100,
            "forks_count": 50,
            "open_issues_count": 10
        }
    ]
    with patch("ingest.GitHubClient") as MockClient:
        MockClient.return_value = mock_github_client
        with patch("ingest.get_all_companies", return_value = ["anthropic"]):
            with patch("ingest.get_connection", return_value= mock_conn):
                with patch("db.execute_values"):
                    run_ingestion()
                    # assert "Unexpected GitHub API response format" in caplog.text
                
def test_ingestion_with_missing_owner(mock_conn, mock_github_client, caplog):
    mock_github_client.getuser_repos.return_value = [
        {
            "id": 1000,
            "name": "test-repo",
            "full_name": "anthropic/test-repo",
            "language": "Python",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-02",
            "stargazers_count": 100,
            "forks_count": 50,
            "open_issues_count": 10
        }
    ]
    with patch("ingest.GitHubClient") as MockClient:
        MockClient.return_value = mock_github_client
        with patch("ingest.get_all_companies", return_value = ["anthropic"]):
            with patch("ingest.get_connection", return_value= mock_conn):
                with patch("db.execute_values"):
                    run_ingestion()
                    # assert "Repo missing owner. Skipping." in caplog.text
                    
def test_ingestion_repo_with_no_languages(mock_conn, mock_github_client, caplog):
    mock_github_client.get_user_repos.return_value = [
        {
            "id": 1000,
            "owner": {"id": 12345, "login": "anthropic"},
            "name": "test-repo",
            "full_name": "anthropic/test-repo",
            "language": "Python",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-02",
            "stargazers_count": 100,
            "forks_count": 50,
            "open_issues_count": 10
        }
    ]
    
    mock_github_client.get_repo_languages.return_value = None
    
    with patch("ingest.GitHubClient") as MockClient:
        MockClient.return_value = mock_github_client
        with patch("ingest.get_all_companies", return_value = ["anthropic"]):
            with patch("ingest.get_connection", return_value= mock_conn):
                with patch("db.execute_values"):
                    with patch("ingest.get_all_languages", return_value= {"Python" : 1}):
                        run_ingestion()
                        # assert "No languages detected for repo anthropic" in caplog.text
                        
def test_ingestion_cleanup_called(mock_conn, mock_github_client):
    mock_github_client.get_user_repos.return_value = [
        {
            "id": 1000,
            "owner": {"id": 12345, "login": "anthropic"},
            "name": "test-repo",
            "full_name": "anthropic/test-repo",
            "language": "Python",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-02",
            "stargazers_count": 100,
            "forks_count": 50,
            "open_issues_count": 10
        }
    ]
    mock_github_client.get_repo_languages.return_value = {"Python": 5000}
    
    with patch("ingest.GitHubClient") as MockClient:
        MockClient.return_value = mock_github_client
        with patch("ingest.get_all_companies", return_value=["anthropic"]):
            with patch("ingest.get_connection", return_value=mock_conn):
                with patch("db.execute_values"):
                    with patch("ingest.get_all_languages", return_value= {"Python" : 1}):
                        with patch("ingest.clean_up_db") as  mock_cleanup:
                            run_ingestion()
                            mock_cleanup.assert_called_once()
        