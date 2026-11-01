#!/usr/bin/env bash
# One-off (2026-11-01): DAS moved from Continuum application #14 to #21.
# Files the DAS v1.3.3 README and its two standards under #21, then removes the
# orphaned records of #14 (old DAS) and #5 (DoDAF Pipeline, retired).
# Run where REPO_API_KEY is set (the Repository's .env):  bash scripts/refile_das_2026-11-01.sh
set -euo pipefail
: "${REPO_API_KEY:?set REPO_API_KEY first}"
API="${REPO_URL:-https://repo.k9x.ai}/api/v1"
H=(-H "X-API-Key: $REPO_API_KEY" -H "Content-Type: application/json")

echo "1. README (DAS v1.3.3) -> application/21"
README=$(curl -fsS https://raw.githubusercontent.com/k9aif/dow-k9x/v1.3.3/README.md)
python3 -c 'import json,sys; print(json.dumps({
  "entity_type": "application", "entity_id": 21, "entity_name": "Defense Acquisition System (DAS)",
  "artifact_type": "doc", "filename": "README.md", "mime_type": "text/markdown",
  "content_text": sys.stdin.read(), "version": "1.3.3",
  "git_ref": "https://github.com/k9aif/dow-k9x/tree/v1.3.3",
  "captured_by": "ravinatarajan@k9x.ai", "business_unit": "Defense & Public Sector"}))' <<<"$README" \
  | curl -fsS -X POST "${H[@]}" --data @- "$API/artifacts" >/dev/null && echo "   ok"

echo "2. standards (TOGAF 10 = 2, DoDAF 2.02 = 3) -> application/21"
for sid in 2 3; do
  curl -fsS -X POST "${H[@]}" "$API/standards/link" \
    -d "{\"entity_type\":\"application\",\"entity_id\":21,\"entity_name\":\"Defense Acquisition System (DAS)\",\"standard_id\":$sid}" >/dev/null && echo "   linked $sid"
done

echo "3. remove orphaned artifacts: 15 (old DAS #14), 14 (DoDAF Pipeline #5)"
for aid in 15 14; do
  curl -fsS -X DELETE -H "X-API-Key: $REPO_API_KEY" "$API/artifacts/$aid" && echo "   deleted $aid"
done

echo "Check: $API/entities/application/21"
