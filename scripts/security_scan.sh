#!/usr/bin/env bash
# Security baseline scan — local mirror of the CI security gate.
# Runs: (1) gitleaks secret scan, (2) pip-audit dependency scan.
# Exit non-zero if EITHER finds an unresolved issue, so it can gate a merge.
#
# Usage:  bash scripts/security_scan.sh
# Requires: gitleaks (https://github.com/gitleaks/gitleaks), pip-audit (pip install pip-audit).
# Both checks are release-blocking under docs/ENGINEERING_STANDARDS.md (security >= 99%).

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

status=0

echo "=== [1/2] Secret scan (gitleaks) ==="
if command -v gitleaks >/dev/null 2>&1; then
  if gitleaks detect --config .gitleaks.toml --redact --no-banner --source .; then
    echo "PASS: no secrets detected."
  else
    echo "FAIL: gitleaks found potential secrets (see above). BLOCKING."
    status=1
  fi
else
  echo "ERROR: gitleaks not installed. Install it before requesting a security pass."
  echo "       https://github.com/gitleaks/gitleaks#installing"
  status=1
fi

echo
echo "=== [2/2] Dependency scan (pip-audit) ==="
if command -v pip-audit >/dev/null 2>&1; then
  target="backend/requirements.txt"
  if [ -f "$target" ]; then
    audit_cmd=(pip-audit -r "$target")
  else
    echo "NOTE: $target not found; auditing backend/ project metadata instead."
    echo "      Generate a lockfile for reproducible scans (see docs/security/dependency-scanning.md)."
    audit_cmd=(pip-audit --path backend)
  fi
  if "${audit_cmd[@]}"; then
    echo "PASS: no known-vulnerable dependencies with fixes available."
  else
    echo "FAIL: pip-audit found vulnerable dependencies (see above). BLOCKING unless triaged + signed off."
    status=1
  fi
else
  echo "ERROR: pip-audit not installed (pip install pip-audit)."
  status=1
fi

echo
if [ "$status" -eq 0 ]; then
  echo "=== SECURITY BASELINE: PASS ==="
else
  echo "=== SECURITY BASELINE: FAIL (blocking) ==="
fi
exit "$status"
