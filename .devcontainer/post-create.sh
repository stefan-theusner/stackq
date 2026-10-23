#!/usr/bin/env bash
set -euo pipefail

# Install psql 18 from the official PostgreSQL apt repo (Debian's default is older)
sudo apt-get update
sudo apt-get install -y --no-install-recommends postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y
sudo apt-get install -y --no-install-recommends postgresql-client-18

# Install mise and activate it for future shells
curl -fsSL https://mise.run | sh
export PATH="$HOME/.local/bin:$PATH"
echo 'eval "$(~/.local/bin/mise activate bash)"' >> ~/.bashrc
echo 'eval "$(~/.local/bin/mise activate zsh)"' >> ~/.zshrc 2>/dev/null || true

# Install Python from mise.toml (postgres is skipped: it runs in the db container)
mise trust
mise install python
mise run install

echo "✅ stackq devcontainer ready. Ollama is expected on the host at \$OLLAMA_HOST."
