#!/usr/bin/env bash

set -ex

mkdir -p "$HOME/.local/bin"

curl -fLsS \
    https://github.com/casey/just/releases/download/v0.4.4/just-v0.4.4-x86_64-unknown-linux-musl.tar.gz \
    | tar xz -C "$HOME/.local/bin" just
