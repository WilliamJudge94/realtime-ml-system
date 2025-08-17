#!/bin/bash

# Install tools specified in mise.toml
#
WORKSPACE_DIR="/workspaces/$(basename "$PWD")"
if [ -d "$WORKSPACE_DIR" ]; then
    cd "$WORKSPACE_DIR"
else
    echo "Workspace directory not found, using current directory: $PWD"
fi

mise trust
mise install

# Configure mise to enable idiomatic version files for Python
# This removes the deprecation warning and ensures .python-version files work
mise settings add idiomatic_version_file_enable_tools python

echo 'eval "$(/usr/local/bin/mise activate bash)"' >> ~/.bashrc
source ~/.bashrc
