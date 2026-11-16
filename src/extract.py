import logging

logger = logging.getLogger(__name__)

def extract(client, companies, last_run):
    raw = []
    for company in companies:
        repos = client.get_user_repos(company, since=last_run.get(company))

        if not isinstance(repos, list):
            logger.error("Unexpected GitHub API response format")
            continue

        if not repos:
            logger.warning(f"No repos returned for {company}")
            continue

        for repo in repos:
            owner = repo.get("owner")
            if repo.get("id") and owner:
                languages = client.get_repo_languages(owner["login"], repo["name"])
                if not languages:
                    logger.warning(f"No languages detected for repo {repo['name']}")
            else:
                languages = None   
            raw.append({**repo, "languages": languages})

    return raw