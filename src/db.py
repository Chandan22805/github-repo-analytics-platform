import psycopg2
from psycopg2.extras import execute_values

from config import DB_URL

def get_connection():
    return psycopg2.connect(DB_URL)

def bulk_insert_companies(conn, companies:dict):
    if not companies: return
    
    cursor = conn.cursor()
    
    query = """
            INSERT INTO companies(id, name)
            VALUES %s
            ON CONFLICT (id) DO NOTHING;
        """
    
    values = [(cid, name) for cid, name in companies.items()]
    
    execute_values(cursor, query, values)
    cursor.close()
    
def bulk_insert_repos(conn, repos:dict):
    if not repos: return
    cursor = conn.cursor()
    
    query = """
            INSERT INTO repos(id, company_id, name, full_name, language, created_at, updated_at)
            VALUES %s
            ON CONFLICT (id) DO NOTHING;
        """
    
    values = list(repos.values())
    
    execute_values(cursor, query, values)
    cursor.close()
    
def bulk_insert_snapshots(conn, snapshots: list):
    if not snapshots: return
    cursor = conn.cursor()
    
    query = """
            INSERT INTO repo_snapshots(
                repo_id, snapshot_date, stars, forks, open_issues
            )
            VALUES %s
            ON CONFLICT (repo_id, snapshot_date) DO NOTHING;
        """
  
    execute_values(cursor, query, snapshots)
    cursor.close()