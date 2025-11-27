PYTHON := python
QUERY ?= Analyze ROAS drop in last 7 days

.PHONY: install run test lint report

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) src/run.py "$(QUERY)"

test:
	pytest -q

lint:
	$(PYTHON) -m compileall src

report:
	$(PYTHON) src/run.py "Analyze ROAS drop in last 7 days"
