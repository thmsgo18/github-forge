#!/usr/bin/env bash
# Applies github-forge settings to a GitHub repository.
# Usage: configure-repo.sh OWNER/REPO [--releases]
set -euo pipefail
R=${1:?"Usage: configure-repo.sh OWNER/REPO [--releases]"}
RELEASES=false
[ "${2:-}" = "--releases" ] && RELEASES=true

echo "→ Fusion : squash uniquement, titre de PR = message de commit, branches supprimées après fusion"
gh api -X PATCH "repos/$R" --silent \
  -F allow_squash_merge=true -F allow_merge_commit=false -F allow_rebase_merge=false \
  -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=PR_BODY \
  -F delete_branch_on_merge=true -F allow_auto_merge=true -F allow_update_branch=true

if [ "$(gh api "repos/$R" --jq .visibility)" = public ]; then
  echo "→ Sécurité : scan des secrets et blocage des push qui en contiennent"
  printf '%s' '{"security_and_analysis":{"secret_scanning":{"status":"enabled"},"secret_scanning_push_protection":{"status":"enabled"}}}' \
    | gh api -X PATCH "repos/$R" --input - --silent || echo "  ⚠ impossible d'activer le scan des secrets"
else
  echo "  ⚠ dépôt privé : le scan des secrets demande GitHub Secret Protection (payant), étape ignorée"
fi

echo "→ Dependabot : alertes de vulnérabilités et correctifs de sécurité automatiques"
gh api -X PUT "repos/$R/vulnerability-alerts" --silent || echo "  ⚠ alertes Dependabot non activées"
gh api -X PUT "repos/$R/automated-security-fixes" --silent || echo "  ⚠ correctifs automatiques non activés"

if $RELEASES; then
  echo "→ Workflows : lecture seule par défaut, création de PR autorisée (pour release-please)"
else
  echo "→ Workflows : lecture seule par défaut"
fi
gh api -X PUT "repos/$R/actions/permissions/workflow" --silent \
  -f default_workflow_permissions=read -F can_approve_pull_request_reviews=$RELEASES

echo
echo "Récapitulatif de $R :"
gh api "repos/$R" --jq '
  "  fusion squash seule        : \(.allow_squash_merge and (.allow_merge_commit|not) and (.allow_rebase_merge|not))",
  "  message du commit de squash : \(.squash_merge_commit_title) + \(.squash_merge_commit_message)",
  "  branches supprimées         : \(.delete_branch_on_merge)",
  "  auto-merge                  : \(.allow_auto_merge)",
  "  scan des secrets            : \(.security_and_analysis.secret_scanning.status // "n/a")",
  "  blocage des push à secret   : \(.security_and_analysis.secret_scanning_push_protection.status // "n/a")"'
