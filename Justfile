# Show this message and exit.
help:
    @just --list

# Completely removing anything not tracked by Git.
pristine:
    git reset --hard && git clean -dfx

# Remove all build artefacts.
clean:
    rm -rf build dist wheels
    find . \( -name *.pyc -o -name *.pyo -o -name __pycache__ -o -name *.egg-info \) -exec rm -rf {} +

# Install package.
install:
    pip install -e ".[ext]"

# Install package and development dependencies.
install-dev:
    pip install -r dev-requirements.in -e ".[ext]"

# Run all lints.
lint:
    black --check --diff .
    isort --check --diff .
    flake8 --max-complexity 10 .

# Sort import statements and run black.
fmt:
    black .
    isort .

# Run all tests.
test:
    pytest -xvv --cov=serde --cov-report xml --cov-report term-missing --cov-fail-under 100 tests

# Compile docs.
docs:
    make -C docs html

# Clean docs.
docs-clean:
    make -C docs clean

# Compile and open the docs.
docs-open: docs
    open docs/_build/html/index.html
