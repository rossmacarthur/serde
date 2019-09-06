#!/usr/bin/env bash

set -ex

if [ "$COVERAGE" = true ]; then
    codecov
fi
