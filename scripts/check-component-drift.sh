#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$ROOT/mobile-stack.json"
STRICT=0
MANIFEST_ONLY=0

usage() {
  cat <<'USAGE'
Usage: scripts/check-component-drift.sh [--strict] [--manifest-only]

Checks local component repos listed in mobile-stack.json against their expected
branches. The check is read-only and uses only Python stdlib plus git.

Options:
  --strict         Return non-zero when a repo is missing, dirty, or on a different branch.
  --manifest-only  Parse and print manifest entries without requiring local repo paths.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --strict)
      STRICT=1
      ;;
    --manifest-only)
      MANIFEST_ONLY=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required" >&2
  exit 2
fi

if [ "$MANIFEST_ONLY" -eq 0 ] && ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is required unless --manifest-only is used" >&2
  exit 2
fi

status=0

while IFS=$'\t' read -r name path branch owner; do
  if [ -z "$name" ]; then
    continue
  fi

  if [ "$MANIFEST_ONLY" -eq 1 ]; then
    printf 'manifest\t%s\tbranch=%s\towner=%s\tpath=%s\n' "$name" "$branch" "$owner" "$path"
    continue
  fi

  if [ ! -d "$path/.git" ]; then
    printf 'missing\t%s\texpected_branch=%s\tpath=%s\n' "$name" "$branch" "$path"
    status=1
    continue
  fi

  current_branch="$(git -C "$path" rev-parse --abbrev-ref HEAD 2>/dev/null || printf unknown)"
  dirty="clean"
  if [ -n "$(git -C "$path" status --porcelain 2>/dev/null)" ]; then
    dirty="dirty"
  fi

  relation="ok"
  if [ "$current_branch" != "$branch" ]; then
    relation="branch-drift"
    status=1
  fi
  if [ "$dirty" = "dirty" ]; then
    status=1
  fi

  printf '%s\t%s\tcurrent=%s\texpected=%s\tworktree=%s\towner=%s\n' "$relation" "$name" "$current_branch" "$branch" "$dirty" "$owner"
done < <(python3 - "$CONFIG" <<'PY'
import json
import sys
from pathlib import Path

config = json.loads(Path(sys.argv[1]).read_text())
for name, repo in config.get("repos", {}).items():
    print("\t".join([name, repo.get("path", ""), repo.get("branch", ""), repo.get("owner", "")]))
PY
)

if [ "$STRICT" -eq 1 ]; then
  exit "$status"
fi

exit 0
