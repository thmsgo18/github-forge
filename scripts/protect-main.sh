#!/usr/bin/env bash
# Creates or updates the "Protect main" ruleset on the default branch.
# Usage: protect-main.sh OWNER/REPO solo|team [--signatures|--no-signatures] [REQUIRED_CHECK ...]
#   solo : PR required, no approval (GitHub forbids approving your own PR), signed commits required
#   team : + 1 approval, stale approvals dismissed, conversations resolved, branch up to date;
#          signed commits not required (every teammate would have to sign)
#   --signatures / --no-signatures override the signed-commit default. GitHub checks every commit
#   of a PR, even with squash merge, so require signatures only once every author's key is on GitHub.
# Run it only once the CI workflows exist on main, so the required check names are known.
set -euo pipefail
USAGE="Usage: protect-main.sh OWNER/REPO solo|team [--signatures|--no-signatures] [CHECK ...]"
R=${1:?"$USAGE"}
MODE=${2:?"$USAGE"}
shift 2
case "$MODE" in
  solo) SIGN=true ;;
  team) SIGN=false ;;
  *) echo "Mode inconnu : $MODE (solo ou team)" >&2; exit 2 ;;
esac
CHECKS=()
for arg in "$@"; do
  case "$arg" in
    --signatures) SIGN=true ;;
    --no-signatures) SIGN=false ;;
    -*) echo "Option inconnue : $arg" >&2; echo "$USAGE" >&2; exit 2 ;;
    *) CHECKS+=("$arg") ;;
  esac
done

BODY=$(python3 - "$MODE" "$SIGN" ${CHECKS[@]+"${CHECKS[@]}"} <<'PY'
import json, sys
mode, sign, checks = sys.argv[1], sys.argv[2] == "true", sys.argv[3:]
team = mode == "team"
rules = [
    {"type": "deletion"},
    {"type": "non_fast_forward"},
    {"type": "required_linear_history"},
    {"type": "pull_request", "parameters": {
        "required_approving_review_count": 1 if team else 0,
        "dismiss_stale_reviews_on_push": team,
        "require_code_owner_review": False,
        "require_last_push_approval": False,
        "required_review_thread_resolution": team,
        "allowed_merge_methods": ["squash"],
    }},
]
if sign:
    rules.append({"type": "required_signatures"})
if checks:
    rules.append({"type": "required_status_checks", "parameters": {
        "strict_required_status_checks_policy": team,
        "required_status_checks": [{"context": c} for c in checks],
    }})
print(json.dumps({
    "name": "Protect main",
    "target": "branch",
    "enforcement": "active",
    "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
    "bypass_actors": [],
    "rules": rules,
}))
PY
)

# Explains why GitHub refused, with the right offer for a personal account or an organization.
plan_hint() {
  if [ "$(gh api "repos/$R" --jq .owner.type 2>/dev/null)" = Organization ]; then
    echo "⚠ Dépôt privé d'une organisation gratuite : les rulesets demandent l'offre GitHub Team (payante) ou un dépôt public." >&2
    echo "  Le Student Pack ne s'applique pas aux organisations. En attendant, installe la garde locale de main (references/team.md § « Sans protection GitHub »)." >&2
  else
    echo "⚠ Les rulesets d'un dépôt privé demandent GitHub Pro (gratuit avec le GitHub Student Pack) ou un dépôt public." >&2
  fi
}

# Read the existing rulesets first: on a refusal, gh prints the error body on stdout,
# which must never be mistaken for a ruleset id.
if ! LIST=$(gh api "repos/$R/rulesets" 2>&1); then
  echo "$LIST" >&2
  if echo "$LIST" | grep -qiE "upgrade|403"; then plan_hint; fi
  exit 1
fi
ID=$(printf '%s' "$LIST" | python3 -c '
import json, sys
print(next((str(r["id"]) for r in json.load(sys.stdin) if r.get("name") == "Protect main"), ""))')
if [ -n "$ID" ]; then
  echo "→ Mise à jour du ruleset « Protect main » (#$ID), mode $MODE, commits signés exigés : $SIGN"
  METHOD=PUT; ENDPOINT="repos/$R/rulesets/$ID"
else
  echo "→ Création du ruleset « Protect main », mode $MODE, commits signés exigés : $SIGN"
  METHOD=POST; ENDPOINT="repos/$R/rulesets"
fi
if ! OUT=$(printf '%s' "$BODY" | gh api -X "$METHOD" "$ENDPOINT" --input - 2>&1); then
  echo "$OUT" >&2
  if echo "$OUT" | grep -qiE "upgrade|403"; then plan_hint; fi
  exit 1
fi

DEFAULT=$(gh api "repos/$R" --jq .default_branch)
echo "Règles actives sur $DEFAULT :"
gh api "repos/$R/rules/branches/$DEFAULT" --jq '.[] |
  if .type == "pull_request" then "  - pull_request (approbations : \(.parameters.required_approving_review_count))"
  elif .type == "required_status_checks" then "  - required_status_checks : \([.parameters.required_status_checks[].context] | join(", "))"
  else "  - \(.type)" end'
