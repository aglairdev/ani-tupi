#!/usr/bin/env bash

source="${BASH_SOURCE[0]}"
while [ -h "$source" ]; do
  dir="$( cd -P "$( dirname "$source" )" >/dev/null 2>&1 && pwd )"
  source="$(readlink "$source")"
  [[ $source != /* ]] && source="$dir/$source"
done
dir="$( cd -P "$( dirname "$source" )" >/dev/null 2>&1 && pwd )"

cd "$dir"

if [ -d ".venv" ]; then
    source .venv/bin/activate
    exec python3 main.py "$@"
else
    echo "erro: ambiente virtual (.venv) não encontrado em $dir"
    exit 1
fi
