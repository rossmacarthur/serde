.PHONY: help clean venv install install-all lint sort-imports test docs docs-clean docs-open docs-test dist release

PYTHON := python3
VIRTUAL_ENV := $(or $(VIRTUAL_ENV), $(VIRTUAL_ENV), venv)

help: ## Show this message and exit.
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} \
	/^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

clean: docs-clean ## Remove all build artifacts.
	rm -rf build dist wheels venv *.egg-info
	find . \( -name *.pyc -o -name *.pyo -o -name __pycache__ \) -exec rm -rf {} +

venv: ## Create virtualenv.
	virtualenv --python=$(PYTHON) venv

install: ## Install package.
	$(VIRTUAL_ENV)/bin/pip install -e .

install-travis: ## Install package and linting and testing dependencies.
	$(VIRTUAL_ENV)/bin/pip install -e ".[linting,testing]"

install-all: ## Install package and development dependencies.
	$(VIRTUAL_ENV)/bin/pip install -e ".[linting,testing,documenting,packaging]"

lint: ## Run all lints.
	$(VIRTUAL_ENV)/bin/flake8 --max-complexity 10 .

sort-imports: ## Sort import statements according to isort configuration.
	$(VIRTUAL_ENV)/bin/isort --recursive .

test: ## Run all tests.
	$(VIRTUAL_ENV)/bin/pytest -vv --cov=serde --cov-report term-missing --cov-fail-under 100 --doctest-modules

docs: ## Compile docs.
	$(MAKE) -C docs html

docs-clean: ## Clean docs.
	$(MAKE) -C docs clean

docs-open: docs ## Compile and open the docs.
	open docs/_build/html/index.html

docs-test: ## Run doc tests.
	$(MAKE) -C docs doctest

dist: clean ## Build source and wheel package.
	$(VIRTUAL_ENV)/bin/python setup.py sdist bdist_wheel
	ls -l dist

release: dist ## Package and upload a release.
	$(VIRTUAL_ENV)/bin/twine upload dist/*
