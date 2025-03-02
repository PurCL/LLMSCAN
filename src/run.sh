# #!/bin/bash
# source_bashrc() {
#   if [ -f "$HOME/.bashrc" ]; then
#     . "$HOME/.bashrc"
#   fi
# }

# source_bashrc

python3 scan.py \
  --language=C \
  --inference-model gpt-3.5-turbo-0125 \
  --project-path ../benchmark/C \
  --global-temperature 0.0 \
  --scanners metascan

python3 scan.py \
  --language C++ \
  --inference-model gpt-3.5-turbo-0125 \
  --project-path ../benchmark/C++ \
  --global-temperature 0.0 \
  --scanners metascan