#!/usr/bin/env bash
set -Eeuo pipefail

# Resolve project root (one directory up from this script)
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." &>/dev/null && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs"
VENV_BIN="${PROJECT_ROOT}/.venv/bin"

mkdir -p "${LOG_DIR}"
# Ensure common PATH locations are available under cron
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"

cd "${PROJECT_ROOT}"

# Activate virtualenv if present
if [[ -d "${VENV_BIN}" ]]; then
  # shellcheck disable=SC1091
  source "${VENV_BIN}/activate"
fi

# Timestamped rolling daily log
LOG_FILE="${LOG_DIR}/sync_$(date +%F).log"

# Run the Python job
python main.py >>"${LOG_FILE}" 2>&1
