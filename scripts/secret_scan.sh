#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-repo}"

SECRET_REGEX='-----BEGIN ([A-Z0-9 ]+)?PRIVATE KEY-----|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|xox[baprs]-[A-Za-z0-9-]{10,48}|AIza[0-9A-Za-z_-]{35}'
FORBIDDEN_PATH_REGEX='(^|/)(extension\.pem|id_rsa|id_ed25519)$'
FORBIDDEN_EXT_REGEX='\.pem$|\.key$|\.p12$|\.pfx$'

fail=0

scan_staged() {
  local staged tmp file
  staged="$(git diff --cached --name-only --diff-filter=ACMR || true)"
  if [[ -z "${staged}" ]]; then
    echo "[secret-scan] no staged files to scan"
    return 0
  fi

  tmp="$(mktemp -t hound-secret-scan-staged.XXXXXX)"
  trap 'rm -f "${tmp}"' RETURN

  while IFS= read -r file; do
    [[ -z "${file}" ]] && continue
    if [[ "${file}" =~ ${FORBIDDEN_EXT_REGEX} ]] || [[ "${file}" =~ ${FORBIDDEN_PATH_REGEX} ]]; then
      echo "[secret-scan] blocked file extension/name detected in staged changes: ${file}"
      fail=1
    fi

    if git cat-file -e ":${file}" 2>/dev/null; then
      if git show ":${file}" | grep -nE "${SECRET_REGEX}" >"${tmp}" 2>/dev/null; then
        echo "[secret-scan] potential secret detected in staged file: ${file}"
        sed 's/^/  /' "${tmp}"
        fail=1
      fi
    fi
  done <<< "${staged}"
}

scan_repo() {
  local tmp blocked
  tmp="$(mktemp -t hound-secret-scan-repo.XXXXXX)"
  trap 'rm -f "${tmp}"' RETURN

  blocked="$(git ls-files | grep -E "${FORBIDDEN_EXT_REGEX}|${FORBIDDEN_PATH_REGEX}" || true)"
  if [[ -n "${blocked}" ]]; then
    echo "[secret-scan] blocked secret-like file paths are tracked:"
    sed 's/^/  /' <<< "${blocked}"
    fail=1
  fi

  if git grep -nE "${SECRET_REGEX}" -- . >"${tmp}" 2>/dev/null; then
    echo "[secret-scan] potential secret content found in tracked files:"
    sed 's/^/  /' "${tmp}"
    fail=1
  fi
}

scan_history() {
  local tmp matches
  local patterns=(
    '-----BEGIN PRIVATE KEY-----'
    '-----BEGIN RSA PRIVATE KEY-----'
    '-----BEGIN EC PRIVATE KEY-----'
    '-----BEGIN OPENSSH PRIVATE KEY-----'
  )
  tmp="$(mktemp -t hound-secret-scan-history.XXXXXX)"
  trap 'rm -f "${tmp}"' RETURN

  if git rev-list --all --objects | grep -E '[[:space:]]extension\.pem$' >"${tmp}" 2>/dev/null; then
    echo "[secret-scan] extension.pem still exists in git history:"
    sed 's/^/  /' "${tmp}"
    fail=1
  fi

  for pattern in "${patterns[@]}"; do
    matches="$(git log --all -S "${pattern}" --pretty=format:'%H %ad %s' --date=iso-strict || true)"
    if [[ -n "${matches}" ]]; then
      echo "[secret-scan] private-key header found in commit history (${pattern}):"
      sed 's/^/  /' <<< "${matches}"
      fail=1
    fi
  done
}

case "${MODE}" in
  staged)
    scan_staged
    ;;
  repo)
    scan_repo
    ;;
  history)
    scan_history
    ;;
  all)
    scan_repo
    scan_history
    ;;
  *)
    echo "usage: scripts/secret_scan.sh [staged|repo|history|all]"
    exit 2
    ;;
esac

if [[ "${fail}" -ne 0 ]]; then
  echo "[secret-scan] FAILED"
  exit 1
fi

echo "[secret-scan] clean (${MODE})"
