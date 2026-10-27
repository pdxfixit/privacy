#!/usr/bin/env bash
# take.sh <app> <file>: take an app's privacy policy into this repo. Used by each app's `just policy`.
#
# Copies <file> to src/<app>/policy.md, builds public/, runs `just test`, and commits both. It does not push:
# the app's recipe runs `just land` here afterwards. Nothing changed: it says so and exits 0.
#
# Refuses: an app folder that does not exist, a file that is not a policy (front matter with name:, blurb:
# and updated:), a changed text whose updated: is not a real date, is in the future (UTC), or is not later
# than the site copy's (equal is fine only when it is today, UTC, so a second edit the same day goes in),
# and a checkout with uncommitted changes.
# A failed build or test puts src/<app>/policy.md and public/ back as committed.
#
# Environment: TAKE_MESSAGE is the commit message; else, when TAKE_SHA is set, "docs: <Name>: policy from
# <app>@<short sha>"; else "docs: <Name>: policy from its app".
set -euo pipefail

app=${1:-}
file=${2:-}
if [ -z "$app" ] || [ -z "$file" ]; then
  echo "usage: take.sh <app> <file>" >&2
  exit 2
fi
here=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$here"

fail() { echo "take: $*" >&2; exit 1; }

case "$app" in
  _*|*[!a-z0-9-]*) fail "'$app' is not an app folder name" ;;
esac
[ -d "src/$app" ] || fail "no src/$app here (an app's folder is made on purpose, not by a copy)"
[ -f "$file" ] || fail "$file is not a file"

# A policy starts with a front matter block holding name:, blurb: and updated:.
front() { awk 'NR==1 { if ($0 != "---") exit 1; next } $0 == "---" { ok = 1; exit } { print } END { exit !ok }' "$1"; }
key() { sed -n "s/^$1:[[:space:]]*//p" | head -n 1; }
fm=$(front "$file") || fail "$file does not start with a front matter block (--- … ---)"
for k in name blurb updated; do
  [ -n "$(printf '%s\n' "$fm" | key "$k")" ] || fail "$file has no '$k:' in its front matter, so it is not a policy"
done
name=$(printf '%s\n' "$fm" | key name)
new_updated=$(printf '%s\n' "$fm" | key updated)

[ -z "$(git status --porcelain --untracked-files=no)" ] || fail "uncommitted changes here; commit or stash them first"

dest="src/$app/policy.md"
if [ -f "$dest" ] && ! cmp -s "$file" "$dest"; then
  old_updated=$(front "$dest" | key updated || true)
  # The text changed, so updated: must say so: later than the site copy's, or the same day when that day is today (UTC).
  python3 - "$new_updated" "$old_updated" <<'PY' || exit 1
import datetime, sys
M = "January February March April May June July August September October November December".split()
def parse(s):
    try:
        d, m, y = s.split()
        return datetime.date(int(y), M.index(m) + 1, int(d))
    except ValueError:
        return None
new, old, today = parse(sys.argv[1]), parse(sys.argv[2]), datetime.datetime.now(datetime.timezone.utc).date()
if new is None:
    sys.exit("take: updated: '%s' is not a date like '16 October 2026'" % sys.argv[1])
if new > today:
    sys.exit("take: updated: '%s' is in the future (today is %s, UTC)" % (sys.argv[1], today))
if old is not None and not (new > old or (new == old and new == today)):
    sys.exit("take: updated: '%s' is not later than the site copy's '%s' (the same day only counts when it is today, %s UTC); bump updated: in the app's policy" % (sys.argv[1], sys.argv[2], today))
PY
fi

restore() { git checkout -q HEAD -- "$dest" public 2>/dev/null || true; git clean -fdq -- public 2>/dev/null || true; }
trap 'rc=$?; [ $rc -eq 0 ] || { restore; echo "take: stopped; $dest and public/ are back as committed" >&2; }' EXIT

cp "$file" "$dest"
python3 build.py
just test

git add -- "$dest" public
if git diff --cached --quiet; then
  echo "take: nothing changed; $app's policy here is already current."
  exit 0
fi

if [ -n "${TAKE_MESSAGE:-}" ]; then
  msg=$TAKE_MESSAGE
elif [ -n "${TAKE_SHA:-}" ]; then
  msg="docs: $name: policy from $app@${TAKE_SHA:0:7}"
else
  msg="docs: $name: policy from its app"
fi
git commit -q -m "$msg"
echo "take: committed $(git rev-parse --short HEAD): $msg"
echo "take: now land it: just land"
