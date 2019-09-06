#!/usr/bin/env bash

set -ex

pip install -r ci/requirements/test.txt -e ".[ext]"

if [ "$LINT" = true ]; then
    pip install -r ci/requirements/lint.txt
fi

if [ "$COVERAGE" = true ]; then
    pip install codecov
fi
