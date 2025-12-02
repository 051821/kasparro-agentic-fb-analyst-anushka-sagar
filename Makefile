PYTHON := python
QUERY ?= Analyze ROAS drop in last 7 days

.PHONY: install run test lint logs report

install:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install ruff

run:
	$(PYTHON) src/run.py "$(QUERY)"

test:
	$(PYTHON) -m pytest -q

# WINDOWS-COMPATIBLE RUFF COMMAND
lint:
	.\venv\Scripts\ruff.exe check src/ --fix

logs:
	$(PYTHON) -m src.utils.logs_to_csv

report:
	$(PYTHON) src/run.py "Analyze ROAS drop in last 7 days"
