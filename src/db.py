import psycopg2
from config import DB_URL

def get_connection():
    return psycopg2.connect(DB_URL)
    
def insert_repo(repo_data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
            INSERT INTO repos (id, company_id, name, full_name, language, stars, forks, open_issues, created_at, updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
            ON CONFLICT (id) DO NOTHING;        
        """
    
    values = (
        repo_data["id"],
        repo_data["company_id"],
        repo_data["name"],
        repo_data["full_name"],
        repo_data["language"],
        repo_data["stars"],
        repo_data["forks"],
        repo_data["open_issues"],
        repo_data["created_at"],
        repo_data["updated_at"]
    )
    
    cursor.execute(query,values)
    conn.commit()
    cursor.close()
    conn.close()
    
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