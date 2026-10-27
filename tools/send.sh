#!/usr/bin/env bash
# send.sh <app> <policy file> [--dry-run]: copy an app's privacy policy into this repo and land it.
# Run from the app's repo, by the app's `just policy` (the same recipe in noodlepads, isopix, arrowrama
# and orbit; this is the one place the logic lives, as flarepress's land.sh is for landing).
#
# The decided pattern (Ben, 2026-10-27): each app keeps its policy beside its code, and the agent that
# changes it copies it here in the same task. No CI link, no token, no automatic pull. Run it once the
# change is on the app's main. It:
#   1. refuses when the policy file has uncommitted changes (the copy must match a commit), and, on a real
#      run, when the app's HEAD is not on its origin/main (the sha goes into this repo's history, so it
#      must be a public one; a dry run does not mind);
#   2. fetches this repo and makes a throwaway worktree of its origin/main on a branch of its own (this
#      checkout is never switched or dirtied, and `just land` has a commit to cherry-pick);
#   3. in that worktree runs `just take <app> <file>` with TAKE_SHA set to the app's HEAD, then `just land`,
#      and removes the worktree. A landing that fails keeps the worktree and prints where it is.
# --dry-run stops after the take: it shows the commit that would land and removes the worktree.
# Nothing changed: it says so and lands nothing.
set -euo pipefail

self=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")
here=$(dirname "$(dirname "$self")")
orig=("$@")

die() { echo "send: $*" >&2; exit 1; }

dry=
args=()
for a in "$@"; do
  case "$a" in
    --dry-run) dry=1 ;;
    -*) die "unknown option '$a' (usage: send.sh <app> <policy file> [--dry-run])" ;;
    *) args+=("$a") ;;
  esac
done
[ "${#args[@]}" = 2 ] || die "usage: send.sh <app> <policy file> [--dry-run]"
app=${args[0]}
file=${args[1]}
case "$app" in
  _*|*[!a-z0-9-]*) die "'$app' is not an app folder name" ;;
esac
[ -f "$file" ] || die "$file is not a file (run this from the app's repo: just policy)"
abs=$(cd "$(dirname "$file")" && pwd)/$(basename "$file")

root=$(git -C "$(dirname "$abs")" rev-parse --show-toplevel 2>/dev/null) || die "$file is not in a git repo"
[ -z "$(git -C "$root" status --porcelain --untracked-files=all -- "$abs")" ] \
  || die "$file has uncommitted changes; commit it first (the copy here must match a commit there)"
sha=$(git -C "$root" rev-parse HEAD)

if [ -z "$dry" ]; then
  git -C "$root" fetch -q origin main 2>/dev/null || true
  git -C "$root" merge-base --is-ancestor "$sha" origin/main 2>/dev/null \
    || die "HEAD ${sha:0:7} is not on the app's origin/main yet; land and push it first, then run this from main"
fi

# Pull this repo's main. The checkout itself moves only when it is clean and on main, fast-forward only;
# the work is done in a worktree of origin/main either way. A newer send.sh runs from the top.
base=main
if git -C "$here" fetch -q origin main 2>/dev/null; then
  base=origin/main
  if [ "$(git -C "$here" symbolic-ref -q --short HEAD || true)" = main ] && [ -z "$(git -C "$here" status --porcelain --untracked-files=no)" ]; then
    before=$(git hash-object "$self")
    git -C "$here" merge -q --ff-only origin/main || die "$here: main has diverged from GitHub's; sort that out there first"
    base=main
    if [ -z "${SEND_REEXEC:-}" ] && [ "$(git hash-object "$self" 2>/dev/null || true)" != "$before" ]; then
      SEND_REEXEC=1 exec bash "$self" "${orig[@]}"
    fi
  fi
else
  git -C "$here" rev-parse -q --verify origin/main > /dev/null 2>&1 && base=origin/main
  echo "send: could not reach GitHub; using this repo's $base as it is" >&2
fi
git -C "$here" rev-parse -q --verify "$base" > /dev/null || die "$here has no $base"

git -C "$here" worktree prune
wt=$(mktemp -d "${TMPDIR:-/tmp}/send-privacy.XXXXXX")
branch="send-$app-${sha:0:7}"
cleanup() { git -C "$here" worktree remove --force "$wt" 2>/dev/null || rm -rf "$wt"; git -C "$here" branch -q -D "$branch" 2>/dev/null || true; }
git -C "$here" worktree add -q -b "$branch" "$wt" "$base" \
  || { rm -rf "$wt"; die "could not make a worktree of $here (is branch $branch left from an earlier run? git -C $here branch -D $branch)"; }
[ -e "$wt/tools/take.sh" ] || { cleanup; die "$here's $base has no tools/take.sh yet; the privacy repo's change must land first"; }

start=$(git -C "$wt" rev-parse HEAD)
if ! (cd "$wt" && TAKE_SHA=$sha just take "$app" "$abs"); then
  cleanup
  die "just take stopped (it said why above); nothing was committed"
fi
if [ "$(git -C "$wt" rev-parse HEAD)" = "$start" ]; then
  cleanup
  echo "send: the privacy site already has this policy; nothing to land."
  exit 0
fi

if [ -n "$dry" ]; then
  echo "send: dry run, would land:"
  git -C "$wt" show --stat --format='%h %s' HEAD
  cleanup
  echo "send: dry run done; nothing landed, scratch worktree removed."
  exit 0
fi

if (cd "$wt" && just land); then
  cleanup
  echo "send: landed in the privacy repo; GitHub deploys privacy.pdxfixit.com/$app/. Read its deploy run."
else
  echo "send: just land stopped in $wt (branch $branch). Fix it there and run 'just land-continue $wt' from it, or remove it with: git -C $here worktree remove --force $wt" >&2
  exit 1
fi
