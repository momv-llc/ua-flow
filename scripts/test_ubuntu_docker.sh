#!/usr/bin/env bash
set -euo pipefail

IMAGE="${1:-ubuntu:24.04}"
WORKDIR="/workspace"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to run this script" >&2
  exit 1
fi

echo "Running UA FLOW smoke tests inside ${IMAGE}..."

docker run --rm -t \
  -v "$(pwd)":${WORKDIR} \
  -w ${WORKDIR} \
  ${IMAGE} \
  bash -lc '
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  python3 python3-venv python3-pip \
  nodejs npm git ca-certificates

python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

npm install --prefix frontend --no-package-lock
npm run build --prefix frontend

python -m compileall backend

deactivate
rm -rf .venv
'

echo "Docker smoke tests completed successfully."
