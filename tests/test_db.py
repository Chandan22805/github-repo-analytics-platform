from unittest.mock import MagicMock

import sys
import os

sys.path.insert(0, os.path.abspath("src"))

from src.db import get_last_run
from datetime import date

def test_get_last_run_returns_correct_dict():
    
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        ("anthropic", date(2026, 4, 16)), 
        ("google", date(2026, 4, 16))
    ]

    result = get_last_run(mock_conn)
    
    assert isinstance(result, dict)
    assert result == {"anthropic":date(2026, 4, 16),
                      "google":date(2026, 4, 16)
                    }
    
    assert result.get("anthropic") == date(2026, 4, 16)

if __name__ == "__main__":
    test_get_last_run_returns_correct_dict()
