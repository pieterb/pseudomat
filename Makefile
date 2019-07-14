# The ?= operator below assigns only if the variable isn't defined yet. This
# allows the caller to override them:
#
#     TESTS=other_tests make test

RM = rm -rf
PYTHON = python3
PIP = pip3

# `pytest` and `python -m pytest` are equivalent, except that the latter will
# add the current working directory to sys.path. We don't want that; we want
# to test against the _installed_ package(s), not against any python sources
# that are (accidentally) in our CWD.
PYTEST = pytest

#PYTEST_OPTS    ?= --verbose -p no:cacheprovider --exitfirst --capture=no
PYTEST_OPTS     ?= --verbose -p no:cacheprovider --exitfirst
PYTEST_OPTS_COV ?= $(PYTEST_OPTS) --cov=src --cov-report=term --no-cov-on-fail
TESTS ?= tests



.PHONY: _upgrade_setuptools
_upgrade_setuptools:
	$(PIP) install --upgrade --upgrade-strategy eager setuptools


.PHONY: uninstall
uninstall: _upgrade_setuptools
	-$(PIP) uninstall -y pseudomat


.PHONY: develop
develop: uninstall
	$(PIP) install --upgrade --upgrade-strategy eager -e .[dev,docs,test]
	$(PIP) freeze >requirements_for_intellij.txt


.PHONY: install
install: uninstall
	$(PIP) install --upgrade --upgrade-strategy eager -e .
	$(PIP) freeze >requirements_for_intellij.txt


#.PHONY: sdist
#sdist: clean
#	$(PYTHON) setup.py sdist


#.PHONY: release
#release: clean
#	$(PYTHON) setup.py sdist upload


.PHONY: test
test:
	$(PYTEST) $(PYTEST_OPTS)     $(TESTS)


.PHONY: testcov
testcov:
	$(PYTEST) $(PYTEST_OPTS_COV) $(TESTS)


.PHONY: clean
clean:
	@$(RM) .eggs src/*.egg-info build dist .pytest_cache .coverage
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
