import os
import sys

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
import requests

sys.path.insert(0,os.path.abspath("src"))
from github_client import GitHubClient

def make_response(json_data = None, status = 200, headers = None):
    r = MagicMock()
    r.status_code = status
    r.headers = headers or {}
    r.json.return_value = json_data
    if status >= 400:
        r.raise_for_status.side_effect = requests.exceptions.HTTPError(response=r)
    return r


@pytest.fixture(autouse=True)
def no_sleep():
    with patch("github_client.time.sleep") as s:
        yield s

def test_get_user_repos_paginates_until_empty_page(no_sleep):
    pages = [make_response([{"id":1},{"id":2}]), make_response([])]
    with patch("github_client.requests.get", side_effect = pages) as mock_get:
        repos = GitHubClient().get_user_repos("anthropic")

    assert repos == [{"id":1},{"id":2}]
    assert  mock_get.call_count == 2
    assert mock_get.call_args_list[1].kwargs["params"]["page"] == 2

def test_get_user_repos_retries_on_500_then_succeeds(no_sleep):
    responses = [make_response(status = 500), make_response([{"id":1}]), make_response([])]
    with patch("github_client.requests.get", side_effect=responses):
        repos = GitHubClient().get_user_repos("anthropic")
    assert repos == [{"id":1}]
    no_sleep.assert_called()

def test_get_user_repos_404_raises_without_retry():
    with patch("github_client.requests.get", return_value = make_response(status=404)) as mock_get:
        with pytest.raises(requests.exceptions.HTTPError):
            repos = GitHubClient().get_user_repos("anthropic")
    assert mock_get.call_count == 1

def test_get_user_repos_raises_after_retries_exhausted():
    with patch("github_client.requests.get", return_value = make_response(status = 500)) as mock_get:
        with pytest.raises(requests.exceptions.HTTPError):
            GitHubClient().get_user_repos("anthropic", retries=3)

    assert mock_get.call_count == 3

def test_rate_limit_sleeps_then_retries(no_sleep):
    limited = make_response([], headers = {"X-RateLimit-Remaining":"0", "X-RateLimit-Reset":"0"})
    ok = make_response([])
    with patch("github_client.requests.get", side_effect=[limited,ok]):
        GitHubClient().get_user_repos("anthropic")

    no_sleep.assert_called()

def test_get_repo_language_success():
    with patch("github_client.requests.get", return_value=make_response({"Python":5000})):
        assert GitHubClient().get_repo_languages("anthropic", "repo") == {"Python":5000}

def test_get_repo_languages_requires_owner_and_repo():
    with pytest.raises(ValueError):
        GitHubClient().get_repo_languages("","repo")