#!/usr/bin/env bash

set -ex

if [ "$LINT" = true ]; then
    just lint
fi

if [ "$DOCTESTS" = true ]; then
    just test-all
else
    just test
fi
