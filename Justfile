export VIRTUAL_ENV := env_var("VIRTUAL_ENV")

# Show this message and exit.
help:
    @just --list

# Run any Just command but only if we are using the given Python version.
_python VERSION COMMAND +ARGS='':
    @if $VIRTUAL_ENV/bin/python \
            -c "import platform as p;print ('{} {}'.format(p.python_version(), p.python_implementation()))" \
            | grep -q "^{{ VERSION }}"; then \
        just {{ COMMAND }} {{ ARGS }}; \
    fi

# Completely removing anything not tracked by Git.
pristine:
    git reset --hard && git clean -dfx

# Remove all build artefacts.
clean:
    rm -rf build dist wheels
    find . \( -name *.pyc -o -name *.pyo -o -name __pycache__ -o -name *.egg-info \) -exec rm -rf {} +

# Install package.
install:
    $VIRTUAL_ENV/bin/pip install -e ".[ext]"

# Install package and development dependencies.
install-all:
    $VIRTUAL_ENV/bin/pip install -r dev-requirements.in -e ".[ext]"

_black +ARGS='':
    $VIRTUAL_ENV/bin/black --target-version py27 --skip-string-normalization . {{ ARGS }}

# Run all lints.
lint:
    @just _python '3.[6-9].*C' _black --check
    $VIRTUAL_ENV/bin/flake8 --max-complexity 10 .

# Sort import statements and run black.
blacken:
    $VIRTUAL_ENV/bin/isort --recursive .
    @just _python '3.[6-9].*C' _black

_test +ARGS='':
    $VIRTUAL_ENV/bin/pytest -xvv --cov=serde --cov-report term-missing {{ ARGS }} tests

# Run all tests.
test:
    @just _python '\(2\|3.5\)' _test
    @just _python 3.[6-9] _test --cov-fail-under 100

# Compile docs.
docs:
    make -C docs html

# Clean docs.
docs-clean:
    make -C docs clean

# Compile and open the docs.
docs-open: docs
    open docs/_build/html/index.html
