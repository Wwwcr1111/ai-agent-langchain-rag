#!/bin/bash

echo "🧹 Cleaning environment..."

# Remove virtual environment
rm -rf .venv
rm -rf build/
rm -rf dist/

# Remove Python cache
find . -name '*.pyc' -delete
find . -type d -name '__pycache__' -exec rm -rf {} +
pip cache purge

# Remove test and mypy caches
rm -rf __pycache__ .pytest_cache .mypy_cache

echo "✅ Clean complete."
