FROM debian:bookworm-slim

ARG USERNAME=stackq
ARG USER_UID=1000
ARG USER_GID=1000

# Base tools + psql 18 from the official PostgreSQL apt repo
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates curl git sudo less procps bash-completion nano postgresql-common \
 && /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y \
 && apt-get install -y --no-install-recommends postgresql-client-18 \
 && rm -rf /var/lib/apt/lists/*

# Non-root user with passwordless sudo
RUN groupadd --gid "$USER_GID" "$USERNAME" \
 && useradd --uid "$USER_UID" --gid "$USER_GID" --create-home --shell /bin/bash "$USERNAME" \
 && echo "$USERNAME ALL=(root) NOPASSWD:ALL" > "/etc/sudoers.d/$USERNAME" \
 && chmod 0440 "/etc/sudoers.d/$USERNAME"

# Terminal colors (IDE terminals often start with TERM unset or "dumb")
ENV EDITOR=nano \
    TERM=xterm-256color \
    COLORTERM=truecolor
COPY .devcontainer/bashrc /tmp/stackq-bashrc
RUN cat /tmp/stackq-bashrc >> /etc/bash.bashrc && rm /tmp/stackq-bashrc

# mise lives in a system-wide location and its shims are on PATH via ENV.
# ENV applies to EVERY process in the container (IDE terminals, docker exec,
# login and non-login shells), unlike ~/.bashrc, which only interactive bash reads.
ENV MISE_INSTALL_PATH=/usr/local/bin/mise \
    MISE_DATA_DIR=/opt/mise \
    MISE_CONFIG_DIR=/opt/mise/config \
    MISE_CACHE_DIR=/opt/mise/cache \
    MISE_TRUSTED_CONFIG_PATHS=/workspaces/stackq
ENV PATH=/workspaces/stackq/.venv/bin:/opt/mise/shims:$PATH

RUN curl -fsSL https://mise.run | sh \
 && mkdir -p /opt/mise \
 && chown -R "$USERNAME:$USERNAME" /opt/mise

USER $USERNAME

# Install the Python version pinned in mise.toml and make it the global default
COPY --chown=$USERNAME:$USERNAME mise.toml /tmp/mise/mise.toml
RUN cd /tmp/mise \
 && MISE_TRUSTED_CONFIG_PATHS=/tmp/mise mise install python \
 && mise use --global "python@$(MISE_TRUSTED_CONFIG_PATHS=/tmp/mise mise current python)" \
 && rm -rf /tmp/mise

WORKDIR /workspaces/stackq
