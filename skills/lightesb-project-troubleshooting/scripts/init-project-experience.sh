#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DELIVERY_ROOT="${1:-$(cd "${SKILL_ROOT}/../.." && pwd)}"
TEMPLATE="${SKILL_ROOT}/references/project-experience-template.md"

fail() {
  echo "PROJECT EXPERIENCE INIT REFUSED: $*" >&2
  exit 1
}

[[ -d "${DELIVERY_ROOT}" ]] || fail "delivery directory not found: ${DELIVERY_ROOT}"
[[ -f "${TEMPLATE}" ]] || fail "project experience template not found"

DELIVERY_ROOT="$(cd "${DELIVERY_ROOT}" && pwd)"
PROJECT_DIR="${DELIVERY_ROOT}/project-experience"
PROJECT_FILE="${PROJECT_DIR}/lightesb-project-troubleshooting.md"

mode_output="$("${SCRIPT_DIR}/detect-maintenance-mode.sh" "${DELIVERY_ROOT}")"
if ! grep -qx 'mode=field' <<<"${mode_output}"; then
  fail "project experience can only be initialized in field mode"
fi

[[ ! -L "${PROJECT_DIR}" ]] || fail "project-experience directory must not be a symbolic link"
[[ ! -e "${PROJECT_DIR}" || -d "${PROJECT_DIR}" ]] || fail "project-experience path is not a directory"
[[ ! -L "${PROJECT_FILE}" ]] || fail "project experience file must not be a symbolic link"

if [[ -e "${PROJECT_FILE}" ]]; then
  [[ -f "${PROJECT_FILE}" ]] || fail "project experience path is not a regular file"
  echo "Project experience already exists: ${PROJECT_FILE}"
  exit 0
fi

mkdir -p "${PROJECT_DIR}"
if (set -o noclobber; command cat "${TEMPLATE}" >"${PROJECT_FILE}") 2>/dev/null; then
  echo "Initialized project experience: ${PROJECT_FILE}"
elif [[ -f "${PROJECT_FILE}" && ! -L "${PROJECT_FILE}" ]]; then
  echo "Project experience already exists: ${PROJECT_FILE}"
else
  fail "project experience was not created"
fi
