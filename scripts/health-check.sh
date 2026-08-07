#!/usr/bin/env sh
#
# Probe the Prashn Setu health endpoints.
#
#   ./scripts/health-check.sh                        # http://127.0.0.1:8000
#   ./scripts/health-check.sh http://staging:8000    # explicit base URL
#   PRASHN_API_URL=http://host:8000 ./scripts/health-check.sh
#
# Exit codes are what make this usable from CI, a deploy gate or a cron probe:
#   0  every endpoint returned its expected status
#   1  at least one endpoint returned the wrong status
#   2  the API is unreachable (connection refused / DNS / timeout)
#
# /readyz answering 503 is a correct, meaningful response — it means the app is
# alive but Postgres is not reachable. This script still exits non-zero for it,
# because the question it answers is "is this instance fit to serve traffic".

set -u

BASE_URL="${1:-${PRASHN_API_URL:-http://127.0.0.1:8000}}"
TIMEOUT="${HEALTH_TIMEOUT:-5}"

if [ -t 1 ]; then
    BOLD=$(printf '\033[1m'); RED=$(printf '\033[31m')
    GREEN=$(printf '\033[32m'); DIM=$(printf '\033[2m'); OFF=$(printf '\033[0m')
else
    BOLD=''; RED=''; GREEN=''; DIM=''; OFF=''
fi

failures=0
unreachable=0

# Pretty-print JSON when a python is around; fall back to the raw body so the
# script never fails just because formatting is unavailable.
format_json() {
    if command -v python >/dev/null 2>&1; then
        python -m json.tool 2>/dev/null || cat
    elif command -v python3 >/dev/null 2>&1; then
        python3 -m json.tool 2>/dev/null || cat
    else
        cat
    fi
}

# One-line digest of the OpenAPI document. Printing the whole thing drowns the
# health output it is supposed to sit beside.
summarise_openapi() {
    if command -v python >/dev/null 2>&1; then
        python -c '
import json, sys
try:
    d = json.load(sys.stdin)
except ValueError:
    print("  (unparseable JSON)"); sys.exit()
# ASCII only: python stdout is cp1252 on Windows and mojibakes a UTF-8 dash.
print("  %s v%s | openapi %s | %d path(s): %s" % (
    d.get("info", {}).get("title", "?"),
    d.get("info", {}).get("version", "?"),
    d.get("openapi", "?"),
    len(d.get("paths", {})),
    ", ".join(sorted(d.get("paths", {}))) or "none",
))' 2>/dev/null || echo "  (summary unavailable)"
    else
        echo "  (python not available for summary)"
    fi
}

probe() {
    path="$1"
    expected="$2"
    description="$3"
    render="${4:-body}"

    body_file=$(mktemp)
    # -s quiet, -S still show errors, --max-time bounds a hung server.
    status_and_time=$(
        curl -sS --max-time "$TIMEOUT" \
             -o "$body_file" \
             -w '%{http_code} %{time_total}' \
             "${BASE_URL}${path}" 2>/dev/null
    )
    curl_rc=$?

    printf '%s%s %s%s\n' "$BOLD" "GET" "${BASE_URL}${path}" "$OFF"
    printf '  %s%s%s\n' "$DIM" "$description" "$OFF"

    if [ $curl_rc -ne 0 ]; then
        printf '  %sUNREACHABLE%s (curl exit %d) — is the API running?\n\n' \
               "$RED" "$OFF" "$curl_rc"
        unreachable=$((unreachable + 1))
        failures=$((failures + 1))
        rm -f "$body_file"
        return
    fi

    status=${status_and_time%% *}
    elapsed=${status_and_time##* }

    if [ "$status" = "$expected" ]; then
        printf '  %sHTTP %s%s  expected %s  %ss\n' "$GREEN" "$status" "$OFF" "$expected" "$elapsed"
    else
        printf '  %sHTTP %s%s  expected %s  %ss\n' "$RED" "$status" "$OFF" "$expected" "$elapsed"
        failures=$((failures + 1))
    fi

    if [ -s "$body_file" ]; then
        case "$render" in
            openapi) summarise_openapi < "$body_file" ;;
            none)    : ;;
            *)       format_json < "$body_file" | sed 's/^/  /' ;;
        esac
    fi
    printf '\n'
    rm -f "$body_file"
}

printf '%sPrashn Setu health check%s  %s%s%s\n\n' "$BOLD" "$OFF" "$DIM" "$BASE_URL" "$OFF"

probe /healthz 200 'Liveness. Touches no dependency — must stay 200 even when Postgres is down.'
probe /readyz  200 'Readiness. Runs a real SELECT 1; answers 503 when Postgres is unreachable.'

# Not a health endpoint, but a broken contract breaks the generated TS client,
# so a smoke probe belongs here.
probe /openapi.json 200 'OpenAPI contract the frontend client is generated from.' openapi

if [ "$unreachable" -gt 0 ]; then
    printf '%sAPI unreachable at %s%s\n' "$RED" "$BASE_URL" "$OFF"
    printf 'Start it with:  make dev      (and  make up  for Postgres)\n'
    exit 2
fi

if [ "$failures" -gt 0 ]; then
    printf '%s%d check(s) failed%s\n' "$RED" "$failures" "$OFF"
    exit 1
fi

printf '%sAll checks passed%s\n' "$GREEN" "$OFF"
exit 0
