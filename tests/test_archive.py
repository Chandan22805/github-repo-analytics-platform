import io
import logging
import os
import sys

from datetime import date, timedelta
from unittest.mock import patch, MagicMock

import pyarrow.parquet as pq
import pytest

sys.path.insert(0, os.path.abspath("src"))
from archive import _get_expiring_rows, _rows_to_parquet_buffer, REPO_SCHEMA, export_to_s3

ROWS = [(1, date(2024,1,1), 100, 5, 2)]

def test_parquet_buffer_roundtrip():
    buf = _rows_to_parquet_buffer(ROWS, REPO_SCHEMA)
    table = pq.read_table(buf)
    assert table.schema.equals(REPO_SCHEMA)
    assert table.to_pylist() == [
        {"repo_id":1 , "snapshot_date": date(2024,1,1),"stars":100, "forks":5, "open_issues":2}
    ]

def test_parquet_buffer_empty_rows_returns_none():
    assert _rows_to_parquet_buffer([], REPO_SCHEMA) is None

def test_export_skips_when_no_rows(mock_conn):
    with patch("archive._get_expiring_rows", return_value = ([],[])):
        with patch("archive.boto3.client") as mock_boto:
            export_to_s3(mock_conn)

    mock_boto.assert_not_called()

def test_export_uploads_expected_keys(mock_conn):
    d = (date.today() - timedelta(days=30)).isoformat()
    lang_rows = [(1, date(2024, 1, 1), 7, 5000)]
    with patch("archive._get_expiring_rows", return_value=(ROWS, lang_rows)):
        with patch("archive.boto3.client") as mock_boto:
            export_to_s3(mock_conn)
    s3 = mock_boto.return_value
    keys = [c.args[2] for c in s3.upload_fileobj.call_args_list]
    assert keys == [
        f"github_analytics/repo_snapshots/date={d}/data.parquet",
        f"github_analytics/language_snapshots/date={d}/data.parquet",
    ]

def test_export_raises_after_retries_exhausted(mock_conn):
    with patch("archive._get_expiring_rows", return_value=(ROWS,[])):
        with patch("archive.boto3.client") as mock_boto:
            mock_boto.return_value.upload_fileobj.side_effect = Exception("s3 down")
            with patch("archive.time.sleep"):
                with pytest.raises(Exception):
                    export_to_s3(mock_conn)

    assert mock_boto.return_value.upload_fileobj.call_count == 3

