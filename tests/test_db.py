from unittest.mock  import patch
from conftest import mock_conn

import sys
import os

sys.path.insert(0, os.path.abspath("src"))

from db import get_last_run, get_latest_repo_metrics, get_all_companies, get_latest_language_metrics, get_all_languages, bulk_insert_companies, bulk_insert_language_snapshots, bulk_insert_languages, bulk_insert_repos, bulk_insert_snapshots
from datetime import date

def test_get_last_run(mock_conn):
    mock_conn.cursor().fetchall.return_value = [
        ("anthropic", date(2026, 4, 16)), 
        ("google", date(2026, 4, 16))
    ]

    result = get_last_run(mock_conn)
    
    assert isinstance(result, dict)
    assert result == {"anthropic":date(2026, 4, 16),
                      "google":date(2026, 4, 16)
                    }
    
    assert result.get("anthropic") == date(2026, 4, 16)
    
def test_get_latest_repo_metrics(mock_conn):
    mock_conn.cursor().fetchall.return_value = [
        (10000, 1, 2, 3),
        (10001, 4, 5, 6)
    ]
    
    result = get_latest_repo_metrics(mock_conn)
    
    assert isinstance(result, dict)
    assert result == {
        10000 : (1, 2, 3),
        10001 : (4, 5, 6)
    }
    
    assert result.get(10000) == (1, 2, 3)

def test_get_all_companies(mock_conn):
    mock_conn.cursor().fetchall.return_value = [
        ("anthropic",),
        ("google",)
    ]
    
    result = get_all_companies(mock_conn)
    
    assert isinstance(result ,list)
    assert result == ["anthropic" , "google"]
    
    assert "anthropic" in result
   
def test_get_latest_language_metrics(mock_conn):
    mock_conn.cursor().fetchall.return_value = [
        (1000, 1, 2048),
        (1000, 2, 1024),
        (1001, 2, 4096)
    ]
    
    result = get_latest_language_metrics(mock_conn)
    
    assert isinstance(result, dict)
    assert result == {
        1000 : {1:2048, 2:1024},
        1001 : {2:4096}
    }
    
    assert result[1000][1] == 2048
    assert result[1000][2] == 1024
 
def test_get_all_languages(mock_conn):
    mock_conn.cursor().fetchall.return_value = [
        (1, "python"),
        (2, "java")
    ]
    
    result = get_all_languages(mock_conn)
    
    assert isinstance(result ,dict)
    assert result == {
        "python":1,
        "java":2
    }
    
    assert result.get("python") == 1

def test_bulk_insert_companies_empty(mock_conn):
    bulk_insert_companies(mock_conn, {})
    mock_conn.cursor.assert_not_called()
    
def test_bulk_insert_languages_empty(mock_conn):
    bulk_insert_languages(mock_conn, set())
    mock_conn.cursor.assert_not_called()
    
def test_bulk_insert_repos_empty(mock_conn):
    bulk_insert_repos(mock_conn, {})
    mock_conn.cursor.assert_not_called()
    
def test_bulk_insert_snapshots_empty(mock_conn):
    bulk_insert_snapshots(mock_conn, [])
    mock_conn.cursor.assert_not_called()

def test_bulk_insert_language_snapshots_empty(mock_conn):
    bulk_insert_language_snapshots(mock_conn, [])
    mock_conn.cursor.assert_not_called()

# def test_bulk_insert_companies_non_empty(mock_conn):
#     companies = {12345 : "anthrpoic", 67890:"google"}
    
#     with patch("db.execute_values") as mock_execute:
#         bulk_insert_companies(mock_conn, companies)
#         mock_conn.assert_called_once()

# def test_bulk_insert_languages_non_empty(mock_conn):
#     languages = set(["python", "java"])
#     with patch("db.execute_values") as mock_execute:
#         bulk_insert_languages(mock_conn, languages)
#         mock_conn.assert_called_once()

# def test_bulk_insert_repos_non_empty(mock_conn):

if __name__ == "__main__":
    test_get_last_run()
    test_get_latest_repo_metrics()
    test_get_all_companies()
    test_get_latest_language_metrics()
    test_get_all_languages()
    test_bulk_insert_companies_empty()
    test_bulk_insert_repos_empty()
    test_bulk_insert_languages_empty()
    test_bulk_insert_snapshots_empty()
    test_bulk_insert_language_snapshots_empty()
    # test_bulk_insert_companies_non_empty()
    # test_bulk_insert_languages_non_empty()
