import psycopg2
from psycopg2.extras import execute_values
import datetime

from config import DB_URL

def get_connection():
    return psycopg2.connect(DB_URL)

def bulk_insert_companies(conn, companies:dict):
    if not companies: return
    
    cursor = conn.cursor()
    
    query = """
            INSERT INTO companies(company_id, company_name)
            VALUES %s
            ON CONFLICT (company_id) DO NOTHING;
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

def get_last_run(conn, source: str):
    cursor = conn.cursor()
    
    query = """
            SELECT last_run 
            FROM ingestion_state
            WHERE source = %s; 
            """
        
    values = source
    
    cursor.execute(query, (values,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None
       
def update_last_run(conn, source: str, timestamp):
        cursor = conn.cursor()
        
        query = """
                INSERT INTO ingestion_state (source, last_run)
                VALUES (%s, %s)
                ON CONFLICT(source)
                DO UPDATE SET last_run = EXCLUDED.last_run;
                """
        
        values = [source, timestamp]
        
        cursor.execute(query, values)
        
        cursor.close()

def get_latest_repo_metrics(conn):
    cursor = conn.cursor()
    
    query = """
            SELECT DISTINCT ON(repo_id)
                repo_id,
                stars,
                forks,
                open_issues
            FROM repo_snapshots
            ORDER BY repo_id, snapshot_date DESC;
        """
    
    cursor.execute(query)
    rows =  cursor.fetchall()
    cursor.close()
    return {
        row[0] :(row[1], row[2], row[3])
        for row in rows
    }

def get_all_companies(conn):
    cursor = conn.cursor()
    query = """
            SELECT company_name FROM companies;
            """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    return [name[0] for name in rows]

def bulk_insert_language_snapshots(conn, snapshots: list):
    if not snapshots: return 
    cursor = conn.cursor()
    
    query = """
            INSERT INTO language_snapshots(
                repo_id, snapshot_date, language_id, bytes)
                VALUES %s
                ON CONFLICT (repo_id, snapshot_date, language_id) DO NOTHING
            """
            
    execute_values(cursor, query, snapshots)
    cursor.close()

def get_latest_langauage_metrics(conn):
    cursor = conn.cursor()
    
    query = """
            SELECT DISTINCT ON(repo_id, langauge_id)
                repo_id,
                language_id,
                bytes
            FROM language_snapshots
            ORDER BY repo_id, language_id, snapshot_date DESC
            """

    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    result = {}

    for repo_id, language_id, bytes_ in rows:
        result.setdefault(repo_id, {})[language_id] = bytes_
        
    return result
    
def get_all_languages(conn):
    cursor = conn.cursor()
    
    query = """
            SELECT language_id, language_name FROM languages
            """
            
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    
    return { name: lid for lid,name in rows}

def bulk_insert_languages(conn, languages: set):
    if not languages: return
    cursor = conn.cursor()
    
    query = """
            INSERT INTO languages(language_name)
            VALUES %s
            ON CONFLICT (language_name) DO NOTHING;
        """
    
    values = [(name,) for name in languages]
    
    execute_values(cursor, query, values)
    cursor.close()

def get_latest_language_metrics(conn):
    cursor= conn.cursor()
    
    query = """
            SELECT DISTINCT ON(repo_id, language_id)
                repo_id,
                language_id,
                bytes
            FROM language_snapshots
            ORDER BY repo_id, language_id, snapshot_date DESC;
        """
        
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    result = {}

    for repo_id, language_id, bytes in rows:
        result.setdefault(repo_id, {})[language_id] = bytes
    
    return result
    
