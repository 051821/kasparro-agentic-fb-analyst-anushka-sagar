# tests/test_logs_to_csv.py
import os
import sys

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.logs_to_csv import collect


def test_logs_to_csv_runs(tmp_path):
    try:
        collect()
    except Exception as e:
        assert False, f"collect() crashed: {e}"

    assert True

