import psycopg2
from config import DB_URL

def get_connection():
    return psycopg2.connect(DB_URL)
    
def insert_repo(repo_data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
            INSERT INTO repos (id, company_id, name, full_name, language, created_at, updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s) 
            ON CONFLICT (id) DO NOTHING;        
        """
    
    values = (
        repo_data["id"],
        repo_data["company_id"],
        repo_data["name"],
        repo_data["full_name"],
        repo_data["language"],
        repo_data["created_at"],
        repo_data["updated_at"]
    )
    
    cursor.execute(query,values)
    conn.commit()
    cursor.close()
    conn.close()
    print("Inserted repos")
    
def insert_company(company_data: dict):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
            INSERT INTO companies (id, name)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING;
        """

    values = (
        company_data["id"],
        company_data["name"],
    )

    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()
    print("Inserted company")

def insert_repo_snapshot(snapshot_data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
            INSERT INTO repo_snapshots(
                repo_id, snapshot_date, stars, forks, open_issues
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (repo_id, snapshot_date) DO NOTHING;
        """
  
    values = (
        snapshot_data["repo_id"],
        snapshot_data["snapshot_date"],
        snapshot_data["stars"],
        snapshot_data["forks"],
        snapshot_data["open_issues"],
    )
    
    cursor.execute(query,values)
    conn.commit()
    cursor.close()
    conn.close()
    print("Inserted snapshot")