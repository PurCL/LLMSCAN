#!/bin/bash

# Set the path of the log directory relative to the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/../log"

source_bashrc() {
  if [ -f "$HOME/.bashrc" ]; then
    . "$HOME/.bashrc"
  fi
}

source_bashrc

#bug type: apt, ci, npd, xss, dbz
#model: gpt-3.5-turbo-0125, gpt-4-turbo-preview, gemini, claude-3-haiku-20240307

python scan_sfa.py \
  --inference-model=gpt-3.5-turbo-0125 \
  --project-path=/Users/xiangqian/Documents/CodeBase/LLMSCAN/benchmark/C/openssl \
  --global-temperature=0.0

# python3 scan_sfa.py \
#   --inference-model=gpt-3.5-turbo-0125 \
#   --project-path=/Users/xiangqian/Documents/CodeBase/LLMSCAN/benchmark/C/linux \
#   --global-temperature=0.0