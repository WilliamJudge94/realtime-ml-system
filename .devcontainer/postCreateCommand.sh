#!/bin/bash

# Install tools specified in mise.toml
#
cd /workspaces/real-time-ml-system-cohort-4
mise trust
mise install
echo 'eval "$(/usr/local/bin/mise activate bash)"' >> ~/.bashrc
source ~/.bashrc
