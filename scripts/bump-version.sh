#!/usr/bin/env bash
#
# bump-version.sh -- compute (and optionally tag) the next release version.
#
# The latest `v*` git tag is the only source of the version: setuptools_scm
# derives the package version from it, so there is no file to edit. This
# script prints the next version and, with --tag, creates the `v<X.Y.Z>` tag.
# Publishing a GitHub Release for that tag uploads it to PyPI.
#
# Usage:
#   scripts/bump-version.sh auto                  derive the bump from commits
#   scripts/bump-version.sh <major|minor|patch>   bump a component
#   scripts/bump-version.sh <X.Y.Z>               set an explicit version
#   scripts/bump-version.sh --show                print the current version
#
# `auto` inspects Conventional Commit messages since the last `v*` tag:
#   - a `!` in the type/scope, or `BREAKING CHANGE` in a body -> major
#   - any `feat:` commit                                      -> minor
#   - anything else (fix, chore, ...)                          -> patch
#
# Options:
#   --tag         create an annotated `v<X.Y.Z>` tag on HEAD (not pushed)
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

die() { echo "error: $*" >&2; exit 1; }

last_tag() {
  git -C "$REPO_ROOT" describe --tags --abbrev=0 --match 'v*' 2>/dev/null || true
}

detect_bump() {
  local tag range subjects
  tag="$(last_tag)"
  range="${tag:+${tag}..}HEAD"

  [[ -n "$(git -C "$REPO_ROOT" log "$range" --oneline)" ]] || \
    die "no commits since ${tag:-the start of history}; nothing to bump"

  if git -C "$REPO_ROOT" log "$range" --format='%B' | grep -qE '^BREAKING[ -]CHANGE'; then
    echo major; return
  fi
  subjects="$(git -C "$REPO_ROOT" log "$range" --format='%s')"
  if echo "$subjects" | grep -qE '^[a-z]+[^:]*!:|^[a-z]+[^:]*!\([^:]*\):'; then
    echo major; return
  fi
  if echo "$subjects" | grep -qE '^feat([!(][^:]*)?:'; then
    echo minor; return
  fi
  echo patch
}

BUMP=""
DO_TAG=0

for arg in "$@"; do
  case "$arg" in
    --tag) DO_TAG=1 ;;
    --show)
      tag="$(last_tag)"
      echo "latest tag: ${tag:-(none)}"
      exit 0
      ;;
    -h|--help)
      sed -n '2,23p' "${BASH_SOURCE[0]}" | sed -E 's/^# ?//'
      exit 0
      ;;
    auto|major|minor|patch|*.*.*) BUMP="$arg" ;;
    *) die "unknown argument: $arg" ;;
  esac
done

[[ -n "$BUMP" ]] || die "specify auto, major, minor, patch, or an explicit X.Y.Z version (see --help)"

if [[ "$BUMP" == "auto" ]]; then
  BUMP="$(detect_bump)"
  echo "detected bump from commits: $BUMP"
fi

CURRENT="$(last_tag)"
CURRENT="${CURRENT#v}"
IFS='.' read -r MAJOR MINOR PATCH <<< "${CURRENT:-0.0.0}"

case "$BUMP" in
  major) NEW="$((MAJOR + 1)).0.0" ;;
  minor) NEW="${MAJOR}.$((MINOR + 1)).0" ;;
  patch) NEW="${MAJOR}.${MINOR}.$((PATCH + 1))" ;;
  *)
    [[ "$BUMP" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "invalid version: $BUMP"
    NEW="$BUMP"
    ;;
esac

echo "current version: ${CURRENT:-(none)}"
echo "new version:     $NEW"

if [[ "$DO_TAG" -eq 0 ]]; then
  echo "(not tagged -- pass --tag to create v${NEW})"
  exit 0
fi

git -C "$REPO_ROOT" rev-parse -q --verify "refs/tags/v${NEW}" >/dev/null && die "tag v${NEW} already exists"
git -C "$REPO_ROOT" tag -a "v${NEW}" -m "v${NEW}"
echo "created tag v${NEW}. push it, then publish a GitHub Release for it:"
echo "  git push origin v${NEW} && gh release create v${NEW} --verify-tag --generate-notes"
