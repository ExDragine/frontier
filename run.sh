#!/usr/bin/env bash

export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"

source .venv/bin/activate

while true; do
    uv run nb run
    sleep 5
done
