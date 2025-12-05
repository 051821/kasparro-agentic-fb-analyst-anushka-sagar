import os
import sys
import pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.logger import configure_logging

@pytest.fixture(autouse=True)
def setup_logging(request):
    test_name = request.node.name

    os.environ["PYTEST_ACTIVE"] = "1"
    os.environ["PYTEST_TEST_NAME"] = test_name

    configure_logging()
    yield
