PYTHON := python
QUERY ?= Analyze ROAS drop in last 7 days

.PHONY: install run test lint report

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) src/run.py "$(QUERY)"
	$(PYTHON) src/utils/logs_to_csv.py

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m py_compile $$(git ls-files '*.py')

report:
	$(PYTHON) src/run.py "Analyze ROAS drop in last 7 days"
