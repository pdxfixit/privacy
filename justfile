set shell := ["bash", "-uc"]

# 📋 The recipes
default:
    @just --list

# 🧪 public/ is exactly what src/ builds (the deploy runs the same check), and tools/take.sh behaves
test:
    python3 -m unittest discover -s tests -q
    python3 build.py --check

# 📥 Take an app's policy from its repo: copy the file to src/<app>/policy.md, build, test, commit (no push; then `just land`). TAKE_SHA, TAKE_MESSAGE
take app file:
    bash tools/take.sh {{app}} {{file}}

# Lands through flarepress's shared tool (tools/land.sh in the flarepress checkout beside this one,
# else $FLAREPRESS, else a clone in ~/.cache); land.conf here says what it runs.
# 🛬 Land commits on main: pull it from GitHub, cherry-pick, test, push (GitHub deploys): just land [--wait] [<sha>…]; no sha: this branch's
[positional-arguments]
land *args:
    #!/usr/bin/env bash
    set -euo pipefail
    fp=${FLAREPRESS:-$(cd "$(git rev-parse --git-common-dir)/../.." && pwd)/flarepress}
    [ -e "$fp/tools/land.sh" ] || fp=${XDG_CACHE_HOME:-$HOME/.cache}/flarepress
    [ -e "$fp/tools/land.sh" ] || git clone -q https://github.com/pdxfixit/flarepress "$fp"
    exec bash "$fp/tools/land.sh" "$@"

# 🛬 Finish a landing that stopped on a conflict, once it is resolved in its worktree: just land-continue <worktree>
land-continue worktree:
    @just land --continue {{worktree}}
