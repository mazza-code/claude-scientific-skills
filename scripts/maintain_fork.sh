#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

FIX_BRANCH="codex/fixes-skill-hardening-2026-03-09"
MAIN_BRANCH="main"
ORIGIN_REMOTE="origin"
UPSTREAM_REMOTE="upstream"
PUSH_CHANGES=0
SKIP_TESTS=0
NEW_TAG=""

usage() {
  cat <<'EOF'
Usage: scripts/maintain_fork.sh [options]

Synchronize fork main from upstream, rebase fixes branch, and run regression tests.

Options:
  --push                   Push main and fixes branch updates to origin
  --tag <name>             Create annotated tag on fixes branch tip
  --skip-tests             Skip regression test suite
  --fix-branch <name>      Override fixes branch name
  --main-branch <name>     Override main branch name
  --origin-remote <name>   Override origin remote name (default: origin)
  --upstream-remote <name> Override upstream remote name (default: upstream)
  --help                   Show this help message

Examples:
  scripts/maintain_fork.sh
  scripts/maintain_fork.sh --push
  scripts/maintain_fork.sh --push --tag mazza-skills-fixes-2026-03-09-2
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --push)
      PUSH_CHANGES=1
      shift
      ;;
    --tag)
      NEW_TAG="${2:-}"
      if [[ -z "$NEW_TAG" ]]; then
        echo "Error: --tag requires a value."
        exit 1
      fi
      shift 2
      ;;
    --skip-tests)
      SKIP_TESTS=1
      shift
      ;;
    --fix-branch)
      FIX_BRANCH="${2:-}"
      if [[ -z "$FIX_BRANCH" ]]; then
        echo "Error: --fix-branch requires a value."
        exit 1
      fi
      shift 2
      ;;
    --main-branch)
      MAIN_BRANCH="${2:-}"
      if [[ -z "$MAIN_BRANCH" ]]; then
        echo "Error: --main-branch requires a value."
        exit 1
      fi
      shift 2
      ;;
    --origin-remote)
      ORIGIN_REMOTE="${2:-}"
      if [[ -z "$ORIGIN_REMOTE" ]]; then
        echo "Error: --origin-remote requires a value."
        exit 1
      fi
      shift 2
      ;;
    --upstream-remote)
      UPSTREAM_REMOTE="${2:-}"
      if [[ -z "$UPSTREAM_REMOTE" ]]; then
        echo "Error: --upstream-remote requires a value."
        exit 1
      fi
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Error: Working tree is not clean. Commit/stash changes first."
  exit 1
fi

ORIGINAL_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
cleanup() {
  git checkout "$ORIGINAL_BRANCH" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "Fetching remotes..."
git fetch "$UPSTREAM_REMOTE"
git fetch "$ORIGIN_REMOTE"

echo "Syncing $MAIN_BRANCH from $UPSTREAM_REMOTE/$MAIN_BRANCH..."
git checkout "$MAIN_BRANCH"
git merge --ff-only "$UPSTREAM_REMOTE/$MAIN_BRANCH"

if [[ "$PUSH_CHANGES" -eq 1 ]]; then
  git push "$ORIGIN_REMOTE" "$MAIN_BRANCH"
else
  echo "Skipped push for $MAIN_BRANCH (use --push to enable)."
fi

echo "Rebasing $FIX_BRANCH onto $MAIN_BRANCH..."
git checkout "$FIX_BRANCH"
git rebase "$MAIN_BRANCH"

if [[ "$SKIP_TESTS" -eq 0 ]]; then
  echo "Running regression tests..."
  python3 scientific-skills/scholar-evaluation/scripts/test_calculate_scores.py
  python3 scientific-skills/scientific-schematics/scripts/test_generate_schematic_ai.py
  python3 scientific-skills/citation-management/scripts/test_validate_citations.py
else
  echo "Skipped regression tests."
fi

if [[ "$PUSH_CHANGES" -eq 1 ]]; then
  git push --force-with-lease "$ORIGIN_REMOTE" "$FIX_BRANCH"
else
  echo "Skipped push for $FIX_BRANCH (use --push to enable)."
fi

if [[ -n "$NEW_TAG" ]]; then
  TAG_MESSAGE="Pinned skill fixes snapshot $NEW_TAG"
  git tag -a "$NEW_TAG" -m "$TAG_MESSAGE"
  if [[ "$PUSH_CHANGES" -eq 1 ]]; then
    git push "$ORIGIN_REMOTE" "$NEW_TAG"
  else
    echo "Created local tag $NEW_TAG. Push it with: git push $ORIGIN_REMOTE $NEW_TAG"
  fi
fi

echo "Maintenance workflow complete."
