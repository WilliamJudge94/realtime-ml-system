#!/bin/bash

# Install tools specified in mise.toml
#
cd /workspaces/$(basename $PWD)
mise trust --config-file deployments/common/mise.toml
mise install --config-file deployments/common/mise.toml

# Configure mise to enable idiomatic version files for Python
# This removes the deprecation warning and ensures .python-version files work
mise settings add idiomatic_version_file_enable_tools python

echo 'eval "$(/usr/local/bin/mise activate bash)"' >> ~/.bashrc
source ~/.bashrc
