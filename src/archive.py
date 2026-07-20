import logging
import pyarrow as pa
import pyarrow.parquet as pq
import boto3
import io
import os
from datetime import date, timedelta

logger = logging.getLogger(__name__)

REPO_SCHEMA = pa.schema([
    ("repo_id",         pa.int64()),
    ("snapshot_date",   pa.date32()),
    ("stars",           pa.int64()),
    ("forks",           pa.int64()),
    ("open_issues",     pa.int64()),
])

LANGUAGE_SCHEMA = pa.schema([
    ("repo_id",         pa.int64()),
    ("snapshot_date",   pa.date32()),
    ("language_id",     pa.int64()),
    ("bytes",           pa.int64()),
])

def _get_expiring_rows(conn, days_to_keep:int = 30):
    cursor = conn.cursor()
    query_repo = """
            SELECT * 
            FROM repo_snapshots
            WHERE snapshot_date < CURRENT_DATE - INTERVAL '%s days';
        """
    cursor.execute(query_repo, (days_to_keep,))
    repo_rows = cursor.fetchall()
    
    query_language = """
            SELECT * 
            FROM language_snapshots
            WHERE snapshot_date < CURRENT_DATE - INTERVAL '%s days';
        """
    cursor.execute(query_language, (days_to_keep,))
    language_rows = cursor.fetchall()
    cursor.close()
    return repo_rows,language_rows

def _rows_to_parquet_buffer(rows:list, schema:pa.Schema) -> io.BytesIO:
    if not rows:
        return None

    columns = list(zip(*rows))
    
    arrays = [
        pa.array(col, type=field.type)
        for col,field in zip(columns, schema)
    ]
    
    table = pa.table({field.name: arr for field,arr in zip(schema, arrays)},
                     schema= schema
                     )
    
    buffer = io.BytesIO()
    pq.write_table(table,buffer)
    buffer.seek(0)
    
    return buffer

def export_to_s3(conn, days_to_keep:int = 30):
    
    bucket = os.environ["AWS_BUCKET_NAME"]
    
    expiring_date = date.today() - timedelta(days = days_to_keep)
    
    date_str = expiring_date.isoformat()
    
    repo_rows, language_rows = _get_expiring_rows(conn, days_to_keep)
    
    if not repo_rows and not language_rows:
        logger.info(f"No expiring data found for {date_str}, skipping S# export")
        return 

    logger.info(
        f"Exporting {len(repo_rows)} repo rows and" 
        f"{len(language_rows)} language rows for {date_str} to S3"
        )
    
    s3 = boto3.client("s3")
    
    exports = [
        (repo_rows, REPO_SCHEMA,f"github_analytics/repo_snapshots/date={date_str}/data.parquet"),
        (language_rows, LANGUAGE_SCHEMA,f"github_analytics/language_snapshots/date={date_str}/data.parquet")
    ]
    
    for rows, schema, s3_key in exports:
        buffer = _rows_to_parquet_buffer(rows, schema)
        if buffer is None:
            logger.warning(f"No data for {s3_key}, skipping")
            continue
        
        s3.upload_fileobj(buffer, bucket, s3_key)
        logger.info(f"Upload s3://{bucket}/{s3_key}")