# Ubuntu Docker Smoke Test

This guide describes how to verify that UA FLOW builds successfully inside an Ubuntu-based Docker container. The check ensures that all backend and frontend dependencies install cleanly on a stock Ubuntu 24.04 image and that the compiled artifacts match the repository expectations.

## Prerequisites

- Docker installed on the host machine.
- Network connectivity for installing apt, pip, and npm packages.

## Running the test

```bash
./scripts/test_ubuntu_docker.sh
```

The script performs the following steps inside an `ubuntu:24.04` container:

1. Installs Python 3, Node.js, npm, and supporting packages via `apt`.
2. Creates a virtual environment and installs backend dependencies from `backend/requirements.txt`.
3. Installs frontend dependencies and builds the production bundle with Vite.
4. Compiles the backend with `python -m compileall`.

If you need to target a different base image, pass it as an argument:

```bash
./scripts/test_ubuntu_docker.sh ubuntu:24.04
```

Any failure will stop execution and return a non-zero exit code to help you diagnose missing dependencies or build regressions.
