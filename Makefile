.PHONY: help clean install install-plain install-dev install-all \
		lint sort-imports test test-plain dist release           \
		docs docs-clean docs-open docs-test

VIRTUAL_ENV := $(or $(VIRTUAL_ENV), $(VIRTUAL_ENV), venv)

help: ## Show this message and exit.
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} \
	/^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-13s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

clean: docs-clean ## Remove all build artifacts.
	rm -rf build dist wheels
	find . \( -name *.pyc -o -name *.pyo -o -name __pycache__ -o -name *.egg-info \) -exec rm -rf {} +

install: ## Install package and all features.
	$(VIRTUAL_ENV)/bin/pip install -e ".[toml,yaml]"

install-plain: ## Install package, all features, and testing dependencies.
	$(VIRTUAL_ENV)/bin/pip install -e ".[toml,yaml,dev.test]"

install-dev: ## Install package, all features, and linting and testing dependencies.
	$(VIRTUAL_ENV)/bin/pip install -e ".[toml,yaml,dev.lint,dev.test]"

install-all: install-dev ## Install package, all features, and all development dependencies.
	$(VIRTUAL_ENV)/bin/pip install sphinx twine

lint: ## Run all lints.
	$(VIRTUAL_ENV)/bin/flake8 --max-complexity 10 .

sort-imports: ## Sort import statements according to isort configuration.
	$(VIRTUAL_ENV)/bin/isort --recursive .

test: ## Run all tests.
	$(VIRTUAL_ENV)/bin/pytest -vv --cov=serde --cov-report term-missing --cov-fail-under 100 \
								  --doctest-modules --doctest-import "*<serde"

test-plain: ## Run tests excluding doctests.
	$(VIRTUAL_ENV)/bin/pytest -vv --cov=serde --cov-report term-missing

dist: clean ## Build source and wheel package.
	$(VIRTUAL_ENV)/bin/python setup.py sdist bdist_wheel --universal
	ls -l dist

release: dist ## Package and upload a release.
	$(VIRTUAL_ENV)/bin/twine upload dist/*

docs: ## Compile docs.
	$(MAKE) -C docs html

docs-clean: ## Clean docs.
	$(MAKE) -C docs clean

docs-open: docs ## Compile and open the docs.
	open docs/_build/html/index.html

docs-test: ## Run doc tests.
	$(MAKE) -C docs doctest
