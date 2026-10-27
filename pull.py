#!/usr/bin/env python3
"""Copy the policy of each app listed in pulled.txt from its own repo into src/<app>/policy.md.

    python3 pull.py            # fetch every pulled app and write src/<app>/policy.md (the deploy does this, then builds)
    python3 pull.py --check    # fetch and fail if a committed src/<app>/policy.md differs (writes nothing)

The text is copied exactly: this repo never edits a pulled policy, the app's repo does. Where the file is read
from: PULL_REF (a branch, or the 40-character commit a repository_dispatch names; default main) on
PULL_HOST (default https://raw.githubusercontent.com; a test points it at file:// or a local server).
Stdlib only. Nothing is written unless every app was fetched and looks like a policy.
"""
import os, re, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOST = os.environ.get("PULL_HOST", "https://raw.githubusercontent.com").rstrip("/")
MAX_BYTES = 64 * 1024
REF_OK = re.compile(r"^(main|[0-9a-f]{40})$")


def pulled(listing: Path = ROOT / "pulled.txt"):
    """[(app, repo, path)] from pulled.txt: comments and blank lines skipped, anything else must be three words."""
    rows = []
    for n, line in enumerate(listing.read_text().splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cols = line.split()
        if len(cols) != 3 or not re.fullmatch(r"[a-z0-9-]+", cols[0]) or not re.fullmatch(r"[\w.-]+/[\w.-]+", cols[1]):
            raise SystemExit(f"pulled.txt line {n}: want '<app> <owner/repo> <path>'")
        rows.append(tuple(cols))
    return rows


def fetch(app, repo, path, ref):
    url = f"{HOST}/{repo}/{ref}/{path}"
    try:
        with urllib.request.urlopen(url, timeout=30) as res:
            body = res.read(MAX_BYTES + 1)
    except Exception as e:
        raise SystemExit(f"{app}: could not fetch {url}: {e}")
    if len(body) > MAX_BYTES:
        raise SystemExit(f"{app}: {url} is over {MAX_BYTES} bytes")
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        raise SystemExit(f"{app}: {url} is not UTF-8")
    if not text.startswith("---\n") or "\nname:" not in text.split("\n---\n", 1)[0]:
        raise SystemExit(f"{app}: {url} does not start with a policy's front matter")
    return text


def main(argv):
    ref = os.environ.get("PULL_REF") or "main"
    if not REF_OK.match(ref):
        raise SystemExit(f"PULL_REF must be main or a 40-character commit, not {ref!r}")
    check = "--check" in argv
    fetched = [(app, fetch(app, repo, path, ref)) for app, repo, path in pulled()]  # all fetched before any is written
    stale = 0
    for app, text in fetched:
        dest = ROOT / "src" / app / "policy.md"
        same = dest.exists() and dest.read_text() == text
        print(f"{'same' if same else 'differs' if check else 'wrote'}: {dest.relative_to(ROOT)} (from {ref})")
        if same:
            continue
        if check:
            stale += 1
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text)
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
