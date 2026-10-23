#!/usr/bin/env bash
set -euo pipefail

# psql and Python (via mise) are already baked into the image (see Dockerfile).
# This script only sets up the project's virtualenv.

# Recreate .venv so it points at this container's Python
# (an old .venv may link to a Python from a previous container).
rm -rf .venv
python -m venv .venv
mise run install

# Nice-to-have for interactive shells: load mise.toml env vars on cd
grep -q 'mise activate bash' ~/.bashrc || echo 'eval "$(mise activate bash)"' >> ~/.bashrc

echo "✅ stackq devcontainer ready ($(python --version), $(psql --version))."
echo "   Ollama is expected on the host at $OLLAMA_HOST."
