#!/usr/bin/env bash
# Read-only check that this machine is ready for the github-forge workflow.
# Usage: doctor.sh        Exit code: 0 = ready, 1 = something to fix.
set -u
FAIL=0
ok()   { printf '  ✓ %s\n' "$1"; }
ko()   { printf '  ✗ %s\n    → %s\n' "$1" "$2"; FAIL=$((FAIL + 1)); }
warn() { printf '  ⚠ %s\n    → %s\n' "$1" "$2"; }
cfg()  { git config --global --get "$1" 2>/dev/null; }

echo "Outils"
if command -v git >/dev/null; then ok "git $(git --version | awk '{print $3}')"; else ko "git absent" "brew install git"; fi
if command -v gh >/dev/null; then
  ok "gh $(gh --version | head -1 | awk '{print $3}')"
  STATUS=$(gh auth status -h github.com 2>&1)
  if echo "$STATUS" | grep -q "Logged in"; then
    ok "gh connecté ($(gh api user --jq .login 2>/dev/null))"
    SCOPES=$(echo "$STATUS" | grep -i "token scopes" | head -1)
    for s in repo workflow; do
      if echo "$SCOPES" | grep -q "'$s'"; then ok "scope gh : $s"; else ko "scope gh manquant : $s" "gh auth refresh -h github.com -s $s"; fi
    done
  else
    ko "gh non connecté" "gh auth login"
  fi
else
  ko "gh absent" "brew install gh"
fi
command -v python3 >/dev/null && ok "python3 (scripts du skill)" || ko "python3 absent" "brew install python"

echo "Identité"
NAME=$(cfg user.name); EMAIL=$(cfg user.email)
[ -n "$NAME" ] && ok "user.name = $NAME" || ko "user.name vide" 'git config --global user.name "<pseudo GitHub>"'
case "$EMAIL" in
  *@users.noreply.github.com) ok "user.email = adresse noreply GitHub (e-mail perso masqué)" ;;
  "") ko "user.email vide" "utiliser l'adresse noreply affichée dans GitHub → Settings → Emails" ;;
  *) warn "user.email = $EMAIL (adresse publique dans chaque commit)" "préférer l'adresse noreply de GitHub → Settings → Emails" ;;
esac

echo "Réglages Git"
check_cfg() {
  local key=$1 want=$2 got
  got=$(cfg "$key")
  if [ "$got" = "$want" ]; then ok "$key = $want"; else ko "$key = ${got:-<vide>} (attendu $want)" "git config --global $key $want"; fi
}
check_cfg init.defaultBranch main
check_cfg push.autoSetupRemote true
check_cfg fetch.prune true
check_cfg pull.ff only
check_cfg merge.conflictStyle zdiff3
check_cfg rerere.enabled true

echo "Signature des commits"
KEY=$(cfg user.signingKey); KEY=${KEY/#\~/$HOME}
if [ "$(cfg gpg.format)" = ssh ] && [ "$(cfg commit.gpgSign)" = true ] && [ -n "$KEY" ] && [ -f "$KEY" ]; then
  ok "signature SSH active ($KEY)"
  PUB="${KEY%.pub}.pub"
  if KEYS=$(gh api user/ssh_signing_keys --jq '.[].key' 2>/dev/null); then
    if [ -f "$PUB" ] && echo "$KEYS" | grep -qF "$(awk '{print $2}' "$PUB")"; then
      ok "clé déclarée sur GitHub (badge Verified)"
    else
      ko "clé de signature non déclarée sur GitHub" "gh ssh-key add $PUB --type signing --title \"\$(scutil --get ComputerName) signing key\""
    fi
  else
    warn "impossible de vérifier la clé sur GitHub (scope manquant)" "gh auth refresh -h github.com -s admin:ssh_signing_key"
  fi
else
  ko "signature des commits non configurée" "voir references/machine-setup.md § 5"
fi

echo "Gitignore global"
IG=$(cfg core.excludesFile); IG=${IG:-$HOME/.config/git/ignore}; IG=${IG/#\~/$HOME}
for p in .DS_Store .env .claude/ CLAUDE.md; do
  if grep -qxF "$p" "$IG" 2>/dev/null; then ok "$p ignoré partout"; else ko "$p absent de $IG" "ajouter la ligne « $p » à $IG"; fi
done

echo "Claude Code"
ATTR=$(python3 - <<'PY'
import json, os
try:
    a = json.load(open(os.path.expanduser("~/.claude/settings.json"))).get("attribution")
except Exception:
    a = None
ok = a is False or (isinstance(a, dict) and a.get("commit") == "" and a.get("pr") == "")
print("ok" if ok else "ko")
PY
)
if [ "$ATTR" = ok ]; then ok "attribution désactivée (pas de Co-Authored-By)"; else ko "attribution Claude active" 'ajouter "attribution": {"commit": "", "pr": "", "sessionUrl": false} à ~/.claude/settings.json'; fi
if grep -qi "co-authored-by" ~/.claude/CLAUDE.md 2>/dev/null; then ok "règle « aucune trace d'IA » dans ~/.claude/CLAUDE.md"; else warn "règle absente de ~/.claude/CLAUDE.md" "voir references/machine-setup.md § 6"; fi

echo "Dossier de travail"
ICLOUD="$HOME/Library/Mobile Documents/com~apple~CloudDocs"
case "$PWD/" in
  "$HOME/Documents/"*|"$HOME/Desktop/"*|"$ICLOUD/"*)
    if [ -d "$ICLOUD/Documents" ] || [ -d "$ICLOUD/Desktop" ] || case "$PWD/" in "$ICLOUD/"*) true ;; *) false ;; esac; then
      warn "$PWD est synchronisé par iCloud (copies « 2 », risque pour .git)" "déplacer les projets hors de Documents et du Bureau, par exemple dans ~/Developer (machine-setup.md § 8)"
    else
      ok "dossier de travail hors d'iCloud"
    fi ;;
  *) ok "dossier de travail hors d'iCloud" ;;
esac

echo "Outils optionnels"
command -v pre-commit >/dev/null && ok "pre-commit $(pre-commit --version | awk '{print $2}')" || printf '  · pre-commit absent (installé à la demande pour les projets non-JS)\n'
command -v node >/dev/null && ok "node $(node --version)" || printf '  · node absent\n'

echo
if [ "$FAIL" -eq 0 ]; then echo "✓ Machine prête."; else echo "✗ $FAIL point(s) à corriger."; fi
[ "$FAIL" -eq 0 ]
