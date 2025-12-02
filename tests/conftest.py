# tests/conftest.py
import os
import sys

# Add src to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from utils.logger import configure_logging
import yaml

# Load config
config = yaml.safe_load(open("config/config.yml"))

# Initialize logger ONLY for tests
log_dir = os.path.join(config["paths"]["log_dir"], "tests")
configure_logging(log_dir)
