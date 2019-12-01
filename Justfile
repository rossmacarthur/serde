#!/usr/bin/env just

export PYTHON := "python"
export VIRTUAL_ENV := env_var_or_default("VIRTUAL_ENV", "venv")

# Show this message and exit.
help:
    @just --list

# Remove all build artifacts.
clean:
    rm -rf venv build dist wheels
    find . \( -name *.pyc -o -name *.pyo -o -name __pycache__ -o -name *.egg-info \) -exec rm -rf {} +

# Create a virtualenv.
venv:
    #!/usr/bin/env sh -x
    case "$($PYTHON --version)" in
        "Python 3"*)
            $PYTHON -m venv venv;;
        *)
            virtualenv --python "$PYTHON" venv;;
    esac

# Check the VIRTUAL_ENV variable, and if it is not set create a virtualenv.
check-venv:
    #!/usr/bin/env sh
    if [ "$VIRTUAL_ENV" = "venv" ]; then
        just create-env
    else
        echo "Not creating virtualenv because VIRTUAL_ENV is set."
    fi

# Install package and all features.
install: check-venv
    $VIRTUAL_ENV/bin/pip install -e ".[ext]"

# Install package, all features, and all development dependencies.
install-all: check-venv
    $VIRTUAL_ENV/bin/pip install -r ci/requirements/lint.txt -r ci/requirements/test.txt -e ".[ext]"

# Run all lints.
lint:
    $VIRTUAL_ENV/bin/black --target-version py27 --skip-string-normalization --check .
    $VIRTUAL_ENV/bin/flake8 --max-complexity 10 .

# Blacken and sort import statements
blacken:
    $VIRTUAL_ENV/bin/isort --recursive .
    $VIRTUAL_ENV/bin/black --target-version py27 --skip-string-normalization .

# Run tests excluding doctests.
test:
    $VIRTUAL_ENV/bin/pytest -vv --cov=serde --cov-report term-missing

# Run all tests.
test-all:
    $VIRTUAL_ENV/bin/pytest -vv --cov=serde --cov-report term-missing --cov-fail-under 100 \
                                --doctest-modules --doctest-import "*<serde"

# Build source and wheel package.
dist: clean
    $VIRTUAL_ENV/bin/python setup.py sdist bdist_wheel --universal
    @ls -l dist

# Package and upload a release.
release: dist
    $VIRTUAL_ENV/bin/twine upload dist/*

# Compile docs.
docs:
    make -C docs html

# Clean docs.
docs-clean:
    make -C docs clean

# Compile and open the docs.
docs-open: docs
    open docs/_build/html/index.html
