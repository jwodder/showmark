#!/bin/bash
set -eux

venv_path=/Library/WebServer/Documents/venvs/showmark

cd "$(dirname "$0")"/..

if [ "${1-}" = "--purge" ]
then rm -rf "$venv_path"
     python3 -m venv "$venv_path"
fi

"$venv_path"/bin/pip install .

sudo brew services restart uwsgi
