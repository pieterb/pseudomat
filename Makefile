.PHONY: _upgrade_setuptools uninstall install release sdist clean

RM = rm -rf
PYTHON = python3
PIP = pip3


_upgrade_setuptools:
	$(PIP) install --upgrade --upgrade-strategy eager setuptools


uninstall: _upgrade_setuptools
	-$(PIP) uninstall -y pseudomat


install: uninstall
	$(PIP) install -e .[dev,docs,test]


sdist: clean
	$(PYTHON) setup.py sdist


release: clean
	$(PYTHON) setup.py sdist upload


clean:
	@$(RM) .eggs *.egg-info build dist .pytest_cache .coverage
	@find . -not -path "./.venv/*" -and \( \
		-name "*.pyc" -or \
		-name "__pycache__" -or \
		-name "*.pyo" -or \
		-name "*.so" -or \
		-name "*.o" -or \
		-name "*~" -or \
		-name "._*" -or \
		-name "*.swp" -or \
		-name "Desktop.ini" -or \
		-name "Thumbs.db" -or \
		-name "__MACOSX__" -or \
		-name ".DS_Store" \
	\) -delete
