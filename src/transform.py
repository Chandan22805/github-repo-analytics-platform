import logging

from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass(slots=True)
class ETLBatch:
    repo_snapshots: list
    language_snapshots: list
    companies_to_insert: dict
    repos_to_insert: dict
    languages: set
    changed_repo_ids: set
    last_run: dict

def transform(repos, companies, today) -> ETLBatch:
    repo_snapshots = []
    language_snapshots = []
    companies_to_insert = {}
    repos_to_insert = {}
    languages = set()
    changed_repo_ids = set()
    last_run = {company : today for company in companies}

    for repo in repos:

        if not repo.get("id"):
            logger.warning(f"Repo {repo.get('name')} missing ID: Skipping")
            continue

        if not repo.get("owner"):
            logger.warning(f"Repo {repo.get('name')} missing owner: Skipping")
            continue
        
        company_id = repo["owner"]["id"]
        company_name = repo["owner"]["login"]
        companies_to_insert[company_id] = company_name
        repo_name = repo["name"]
        
        repos_to_insert[repo["id"]] = (
            repo["id"],
            company_id,
            repo_name,
            repo["full_name"],
            repo["language"],
            repo["created_at"],
            repo["updated_at"],
        )
        
        repo_snapshots.append((
            repo["id"],
            today,
            repo["stargazers_count"],
            repo["forks_count"],
            repo["open_issues_count"]
        ))

        changed_repo_ids.add(repo["id"])

        if repo["languages"]:
            for language_name, bytes_ in repo["languages"].items():
                languages.add(language_name)
                
                language_snapshots.append((
                    repo["id"],
                    today,
                    language_name,
                    bytes_
                ))

    return ETLBatch(
        repo_snapshots = repo_snapshots,
        language_snapshots = language_snapshots,
        companies_to_insert = companies_to_insert,
        repos_to_insert = repos_to_insert,
        languages = languages,
        changed_repo_ids = changed_repo_ids,
        last_run = last_run
    )

def carry_forward(batch, latest_repo_metrics, latest_language_metrics, today):

    extra_repo_snapshots = []
    extra_language_snapshots = []

    for repo_id, metrics in latest_repo_metrics.items():
        if repo_id not in batch.changed_repo_ids:
            stars,forks,open_issues = metrics
            extra_repo_snapshots.append((
                repo_id,
                today,
                stars,
                forks,
                open_issues
            ))

    for repo_id, lang_dict in latest_language_metrics.items():
        if repo_id not in batch.changed_repo_ids:
            for language_id, bytes_ in lang_dict.items():
                extra_language_snapshots.append((
                    repo_id,
                    today,
                    language_id,
                    bytes_
                )) 

    return extra_repo_snapshots, extra_language_snapshots