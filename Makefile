.PHONY: run test seed reset install

PYTHON = venv/bin/python
PIP    = venv/bin/pip
FLASK  = venv/bin/flask

run:
	$(PYTHON) app.py

test:
	$(PYTHON) -m pytest -v

seed:
	$(PYTHON) seed.py

reset:
	rm -f instance/recipe_app.db
	FLASK_APP=app.py $(FLASK) db upgrade
	$(PYTHON) seed.py

install:
	$(PIP) install -r requirements.txt
