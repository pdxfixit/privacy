#!/usr/bin/env bash
# After a deploy: privacy.pdxfixit.com serves public/index.html byte for byte, and the
# CSP header is the one public/_headers sets. Read-only GETs. Exit 1 names what failed.
#
# Cloudflare's edge can lag an upload, and for a while different requests get
# different copies: one fetch of the new page proves nothing about the next. So
# the host passes only after NEED matching fetches in a row, within BUDGET seconds;
# any stale fetch starts the count again. A deploy that never settles fails.
#     VERIFY_NEED=5 VERIFY_BUDGET=90 site/verify.sh    # the defaults
set -uo pipefail
cd "$(dirname "$0")/.."
need=${VERIFY_NEED:-5} budget=${VERIFY_BUDGET:-90}
want_csp=$(sed -n 's/^[[:space:]]*Content-Security-Policy:[[:space:]]*//p' public/_headers | head -1)
[ -n "$want_csp" ] || { echo "🛑 no Content-Security-Policy in public/_headers"; exit 1; }
page=$(mktemp)
trap 'rm -f "$page"' EXIT
bad=0
for host in privacy.pdxfixit.com; do
  run=0 hits=0 tries=0 start=$SECONDS
  while [ "$run" -lt "$need" ] && [ $((SECONDS - start)) -lt "$budget" ]; do
    tries=$((tries + 1))
    if curl -fsS -m 20 -o "$page" "https://$host/?$RANDOM$RANDOM" && cmp -s "$page" public/index.html; then
      run=$((run + 1)) hits=$((hits + 1))
    else
      run=0
    fi
    [ "$run" -lt "$need" ] && sleep 1
  done
  took=$((SECONDS - start))
  if [ "$run" -ge "$need" ]; then
    echo "✅ $host serves public/index.html ($need fetches in a row, after ${took}s)"
  else
    echo "❌ $host did not settle on public/index.html: $hits of $tries fetches matched in ${took}s, never $need in a row"
    bad=1
  fi
  got_csp=$(curl -fsS -m 20 -D - -o /dev/null "https://$host/?$RANDOM$RANDOM" | tr -d '\r' | sed -n 's/^[Cc]ontent-[Ss]ecurity-[Pp]olicy:[[:space:]]*//p' | head -1)
  [ "$got_csp" = "$want_csp" ] && echo "✅ $host CSP matches _headers" || { echo "❌ $host CSP differs from _headers"; bad=1; }
done
exit $bad
