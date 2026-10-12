#!/bin/bash
# ============================================================================
# Refresh the Googlebot IP range lookup table
# ============================================================================
# The Cloudflare reports need to tell real Googlebot from fake traffic that
# only copies its user-agent string. Google publishes its crawler IP ranges;
# this loads them into searchconsole.googlebot_ip_ranges. Google updates the
# list periodically, so re-run this about monthly.
# Run from the repository root: ./scripts/refresh_googlebot_ranges.sh
# ============================================================================
set -e

PROJECT="deepdyve-491623"
DATASET="searchconsole"
URL="https://developers.google.com/search/apis/ipranges/googlebot.json"
TMP="$(mktemp -d)"

curl -sfL "$URL" -o "$TMP/ranges.json"

# One row per CIDR prefix (IPv4 and IPv6)
python3 -I - "$TMP/ranges.json" "$TMP/ranges.ndjson" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
with open(sys.argv[2], "w") as out:
    for p in data["prefixes"]:
        cidr = p.get("ipv4Prefix") or p.get("ipv6Prefix")
        out.write(json.dumps({"cidr": cidr}) + "\n")
print(f"{len(data['prefixes'])} prefixes (list created {data['creationTime']})")
PY

bq load --replace --source_format=NEWLINE_DELIMITED_JSON \
    "$PROJECT:$DATASET.googlebot_ip_ranges" "$TMP/ranges.ndjson" cidr:STRING
rm -rf "$TMP"
