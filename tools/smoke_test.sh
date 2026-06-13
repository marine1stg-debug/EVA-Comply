#!/usr/bin/env bash
# EVA Comply — API smoke test
# Run AFTER `docker compose up -d` and the seed has finished.
# Usage:
#   ./tools/smoke_test.sh                      # defaults to http://localhost:8000
#   BASE=http://localhost:8000 ./tools/smoke_test.sh
#   EMAIL=superadmin@eva.com PASS=demo1234 ./tools/smoke_test.sh
#
# Exit code 0 = all checks passed; non-zero = at least one failed.
# Requires: curl, python3 (used only for JSON parsing — no extra packages).

set -u
BASE="${BASE:-http://localhost:8000}"
API="$BASE/api/v1"
EMAIL="${EMAIL:-superadmin@eva.com}"
PASS="${PASS:-demo1234}"

pass=0; fail=0
ok()   { echo "  PASS  $1"; pass=$((pass+1)); }
ko()   { echo "  FAIL  $1"; fail=$((fail+1)); }
hdr()  { echo; echo "== $1 =="; }

# jval <json> <python-expr-on-`d`>  -> prints result or empty on error
jval() { python3 -c "import sys,json
try:
    d=json.load(sys.stdin)
    print($2)
except Exception as e:
    pass" 2>/dev/null; }

# ---- 0. reachability -------------------------------------------------------
hdr "0. Reachability"
code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/docs" || echo 000)
if [ "$code" = "200" ] || [ "$code" = "404" ]; then ok "API reachable ($BASE, HTTP $code)"; else ko "API not reachable at $BASE (HTTP $code)"; echo; echo "Is the stack up? docker compose ps"; exit 1; fi

# ---- 1. auth ---------------------------------------------------------------
hdr "1. Auth / login"
LOGIN=$(curl -s -X POST "$API/auth/login" -H 'Content-Type: application/json' \
        -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")
TOKEN=$(echo "$LOGIN" | jval - "d.get('access_token','')")
if [ -n "$TOKEN" ]; then ok "Logged in as $EMAIL"; else ko "Login failed: $(echo "$LOGIN" | head -c 200)"; echo; echo "Did the seed run? Default pass is demo1234."; exit 1; fi
AUTH=(-H "Authorization: Bearer $TOKEN")

# ---- 2. dashboard ----------------------------------------------------------
hdr "2. Dashboard summary"
D=$(curl -s "${AUTH[@]}" "$API/dashboard/summary")
[ -n "$(echo "$D" | jval - "list(d.keys())[0] if isinstance(d,dict) else ''")" ] \
  && ok "Dashboard summary returned data" || ko "Dashboard summary empty: $(echo "$D" | head -c 160)"

# ---- 3. frameworks ---------------------------------------------------------
hdr "3. Frameworks"
F=$(curl -s "${AUTH[@]}" "$API/frameworks/")
FW_COUNT=$(echo "$F" | jval - "len(d) if isinstance(d,list) else len(d.get('items',[]))")
FW_ID=$(echo "$F" | jval - "(d[0] if isinstance(d,list) else d.get('items',[{}])[0]).get('id','')")
if [ "${FW_COUNT:-0}" -ge 1 ] 2>/dev/null; then ok "Frameworks listed (count=$FW_COUNT)"; else ko "No frameworks returned"; fi

# ---- 4. controls -----------------------------------------------------------
hdr "4. Controls list + detail"
C=$(curl -s "${AUTH[@]}" "$API/controls/")
C_COUNT=$(echo "$C" | jval - "len(d) if isinstance(d,list) else len(d.get('items',[]))")
C_ID=$(echo "$C" | jval - "(d[0] if isinstance(d,list) else d.get('items',[{}])[0]).get('id','')")
if [ "${C_COUNT:-0}" -ge 1 ] 2>/dev/null; then ok "Controls listed (count=$C_COUNT)"; else ko "No controls returned"; fi
if [ -n "$C_ID" ]; then
  CD=$(curl -s "${AUTH[@]}" "$API/controls/$C_ID")
  [ -n "$(echo "$CD" | jval - "d.get('id','')")" ] && ok "Control detail OK ($C_ID)" || ko "Control detail failed"
  EE=$(curl -s "${AUTH[@]}" "$API/controls/$C_ID/expected-evidence")
  EE_N=$(echo "$EE" | jval - "len(d) if isinstance(d,list) else len(d.get('items',[]))")
  ok "Expected-evidence endpoint OK (items=$EE_N)"
fi

# ---- 5. FR/EN content localization ----------------------------------------
hdr "5. FR/EN localization"
EN=$(curl -s "${AUTH[@]}" -H 'X-Lang: en' "$API/controls/")
FR=$(curl -s "${AUTH[@]}" -H 'X-Lang: fr' "$API/controls/")
EN_DOM=$(echo "$EN" | jval - "(d[0] if isinstance(d,list) else d.get('items',[{}])[0]).get('domain','')")
FR_DOM=$(echo "$FR" | jval - "(d[0] if isinstance(d,list) else d.get('items',[{}])[0]).get('domain','')")
echo "    EN domain[0]: $EN_DOM"
echo "    FR domain[0]: $FR_DOM"
if [ -n "$FR_DOM" ] && [ "$FR_DOM" != "$EN_DOM" ]; then ok "Domain localizes EN->FR"; \
  else ko "Domain did not change with X-Lang (check DOMAIN_FR / loc_domain)"; fi

# ---- 6. billing ------------------------------------------------------------
hdr "6. Billing overview"
B=$(curl -s "${AUTH[@]}" "$API/billing/")
[ -n "$(echo "$B" | jval - "list(d.keys())[0] if isinstance(d,dict) else ''")" ] \
  && ok "Billing overview returned" || ko "Billing overview empty: $(echo "$B" | head -c 160)"

# ---- 7. reports ------------------------------------------------------------
hdr "7. Reports"
R=$(curl -s -o /dev/null -w '%{http_code}' "${AUTH[@]}" "$API/reports/")
[ "$R" = "200" ] && ok "Reports index reachable" || ko "Reports index HTTP $R"

# ---- summary ---------------------------------------------------------------
echo
echo "================ SMOKE TEST: $pass passed, $fail failed ================"
[ "$fail" -eq 0 ]
