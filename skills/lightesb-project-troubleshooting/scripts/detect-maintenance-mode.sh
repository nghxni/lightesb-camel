#!/usr/bin/env bash
set -euo pipefail

DELIVERY_ROOT="${1:-$(pwd)}"
SOURCE_ORIGIN="https://gitee.com/nghxni/lightesb.git"

if [[ ! -d "${DELIVERY_ROOT}" ]]; then
  echo "delivery directory not found: ${DELIVERY_ROOT}" >&2
  exit 1
fi

DELIVERY_ROOT="$(cd "${DELIVERY_ROOT}" && pwd)"
origin_url=""
if git -C "${DELIVERY_ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  origin_url="$(git -C "${DELIVERY_ROOT}" config --get remote.origin.url 2>/dev/null || true)"
fi

if [[ "${origin_url}" == "${SOURCE_ORIGIN}" ]]; then
  printf 'mode=local\norigin_match=true\n'
else
  printf 'mode=field\norigin_match=false\n'
fi
