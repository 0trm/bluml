#!/usr/bin/env bash
# Copy the case's files into the empty workspace and build a Python environment
# inside it, so the sandboxed agent can run Python without reading your home folder.
# The data must exist first: uv run evals/make_data.py
set -euo pipefail
case_dir="$(cd "$(dirname "$0")" && pwd)"
if [ ! -d "$case_dir/files/data" ] || [ -z "$(ls "$case_dir/files/data"/*.csv 2>/dev/null)" ]; then
  echo "No data in $case_dir/files/data. Run: uv run evals/make_data.py" >&2
  exit 1
fi
cp -R "$case_dir/files/." .
real_home=$(eval echo "~$(id -un)")
if [ -d "$real_home/.cache/uv" ]; then export UV_CACHE_DIR="$real_home/.cache/uv"; fi
export UV_PYTHON_INSTALL_DIR="$PWD/.python"
uv venv -q --managed-python --python 3.12 .venv
uv pip install -q --python .venv/bin/python --link-mode copy numpy pandas scikit-learn scipy pyarrow
