import logging
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath("src"))

from extract import extract

yesterday = date.today()-timedelta(days=1) 
last_run = {
    "anthropic":yesterday
}

def test_extract_with_empty_companies_list(mock_github_client):
    
    repos = extract(mock_github_client, [], {})
    assert repos == []

def test_extract_with_non_empty_companies_list(mock_github_client):
    
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

    repos = extract(mock_github_client, ["anthropic"], last_run)

    assert repos == [{
        "id": 1000,
        "owner": {"id": 12345, "login": "anthropic"},
        "name": "test-repo",
        "full_name": "anthropic/test-repo",
        "language": "Python",
        "created_at": "2024-01-01",
        "updated_at": "2024-01-02",
        "stargazers_count": 100,
        "forks_count": 50,
        "open_issues_count": 10,
        "languages":{"Python":5000}
    }]
    
    mock_github_client.get_repo_languages.assert_called_once()

def test_extract_with_no_repos_for_a_company(mock_github_client, caplog):

    mock_github_client.get_user_repos.return_value = []
    
    with caplog.at_level(logging.WARNING):
        repos = extract(mock_github_client, ["anthropic"], last_run)

    assert repos == []
    assert "No repos returned for anthropic" in caplog.text

def test_extract_with_improper_format(mock_github_client, caplog):

    mock_github_client.get_user_repos.return_value = {"message": "Bad credentials"}

    with caplog.at_level(logging.ERROR):
        repos = extract(mock_github_client, ["anthropic"], last_run)
            
    assert repos == []
    assert "Unexpected GitHub API response format" in caplog.text   

def test_extract_with_missing_owner(mock_github_client):

    mock_github_client.get_user_repos.return_value = [
        {
            "id": 1000,
            "name": "test-repo",
            "full_name": "anthropic/test-repo",
            "language": "Python",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-02",
            "stargazers_count": 100,
            "forks_count": 50,
            "open_issues_count": 10,
        }
    ]

    repos = extract(mock_github_client, ["anthropic"], last_run)

    assert repos == [
        {
            "id": 1000,
            "name": "test-repo",
            "full_name": "anthropic/test-repo",
            "language": "Python",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-02",
            "stargazers_count": 100,
            "forks_count": 50,
            "open_issues_count": 10,
            "languages":None
        }
    ]
    mock_github_client.get_repo_languages.assert_not_called()

def test_extract_with_missing_repo_id(mock_github_client):

    mock_github_client.get_user_repos.return_value =[ 
        {
            "owner": {"id":1000, "login":"anthropic"},
            "name": "test-repo",
            "full_name": "anthropic/test-repo",
            "language": "Python",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-02",
            "stargazers_count": 100,
            "forks_count": 50,
            "open_issues_count": 10,
        }
    ]

    repos = extract(mock_github_client,["anthropic"],last_run)

    assert repos == [ 
        {
            "owner": {"id":1000, "login":"anthropic"},
            "name": "test-repo",
            "full_name": "anthropic/test-repo",
            "language": "Python",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-02",
            "stargazers_count": 100,
            "forks_count": 50,
            "open_issues_count": 10,
            "languages":None
        }
    ]
    
    mock_github_client.get_repo_languages.assert_not_called()

def test_extract_repo_with_no_languages(mock_github_client,caplog):

    mock_github_client.get_user_repos.return_value=[
        {
            "id": 1000,
            "owner": {"id": 12345, "login": "anthropic"},
            "name": "test-repo",
            "full_name": "anthropic/test-repo",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-02",
            "stargazers_count": 100,
            "forks_count": 50,
            "open_issues_count": 10
        }
    ]

    mock_github_client.get_repo_languages.return_value = None

    with caplog.at_level(logging.WARNING):
        repos = extract(mock_github_client,["anthropic"], last_run)

    assert repos == [
        {
            "id": 1000,
            "owner": {"id": 12345, "login": "anthropic"},
            "name": "test-repo",
            "full_name": "anthropic/test-repo",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-02",
            "stargazers_count": 100,
            "forks_count": 50,
            "open_issues_count": 10,
            "languages":None
        }
    ]
    mock_github_client.get_repo_languages.assert_called_once()
    assert "No languages detected for repo test-repo" in caplog.text

