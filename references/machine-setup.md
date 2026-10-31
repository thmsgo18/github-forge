# Configuration de la machine

À faire une seule fois par ordinateur. `scripts/doctor.sh` vérifie chaque point ci-dessous. Ce guide explique comment corriger ce qui est en rouge.

## 1. GitHub CLI (`gh`)

```bash
brew install gh          # si absent
gh auth login            # GitHub.com → HTTPS → login with a web browser
gh auth status           # doit lister les scopes : repo, workflow (+ admin:ssh_signing_key pour la signature)
```

- `repo` permet de gérer les dépôts, les PR, les issues et les réglages.
- `workflow` est indispensable pour pousser des fichiers dans `.github/workflows/`. Sans lui, le push est refusé.
- `admin:ssh_signing_key` sert uniquement à déclarer la clé de signature sur GitHub.

Pour ajouter un scope, l'utilisateur lance lui-même cette commande : elle ouvre le navigateur pour qu'il autorise l'accès.
```bash
gh auth refresh -h github.com -s admin:ssh_signing_key
```

## 2. Identité Git

```bash
LOGIN=$(gh api user --jq .login); ID=$(gh api user --jq .id)
git config --global user.name "$LOGIN"
git config --global user.email "$ID+$LOGIN@users.noreply.github.com"
```

L'adresse `noreply` garde son vrai e-mail privé tout en reliant les commits à son compte GitHub.

## 3. Réglages Git recommandés

| Réglage | Valeur | Pourquoi |
|---|---|---|
| `init.defaultBranch` | `main` | Les nouveaux dépôts démarrent sur `main` (et pas `master`) |
| `push.autoSetupRemote` | `true` | Le premier `git push` d'une branche fonctionne sans `-u origin …` |
| `fetch.prune` | `true` | Oublie les branches distantes supprimées (après chaque fusion) |
| `pull.ff` | `only` | `git pull` refuse de créer un commit de fusion. S'il échoue sur `main`, c'est qu'on y a commité par erreur |
| `merge.conflictStyle` | `zdiff3` | Les conflits montrent aussi la version d'origine, plus facile à comprendre |
| `rerere.enabled` | `true` | Git se souvient d'une résolution de conflit et la rejoue si le même conflit revient |
| `branch.sort` | `-committerdate` | `git branch` affiche les branches récentes en premier |
| `core.excludesFile` | `~/.config/git/ignore` | Un gitignore global pour tous les dépôts |

```bash
git config --global init.defaultBranch main
git config --global push.autoSetupRemote true
git config --global fetch.prune true
git config --global pull.ff only
git config --global merge.conflictStyle zdiff3
git config --global rerere.enabled true
git config --global branch.sort -committerdate
git config --global core.excludesFile "$HOME/.config/git/ignore"
```

## 4. Gitignore global (`~/.config/git/ignore`)

Ce fichier doit contenir au minimum ces lignes, sans effacer celles qui existent déjà :

```gitignore
# macOS
.DS_Store
.AppleDouble
.LSOverride
._*

# Editors
.idea/
*.swp
*~

# Secrets
.env
.env.local
.env.*.local

# Claude (local only, never published)
.claude/
CLAUDE.md
CLAUDE.local.md
```

Ignorer `.claude/` et `CLAUDE.md` partout garantit qu'aucune trace de l'outil ne part sur GitHub. Ça ne touche pas les fichiers déjà suivis par un dépôt : `scripts/audit-repo.py` les signale.

## 5. Signature des commits (badge « Verified »)

La signature prouve qu'un commit vient bien de l'utilisateur. On utilise une clé SSH ed25519 réservée à cet usage.

```bash
# 1. Clé dédiée, sans phrase de passe (le disque est chiffré par FileVault ; ainsi un commit ne bloque jamais)
ssh-keygen -t ed25519 -C "$(gh api user --jq .login) signing key" -f ~/.ssh/id_ed25519_signing -N ""

# 2. Git signe tous les commits et tags avec cette clé
git config --global gpg.format ssh
git config --global user.signingKey "$HOME/.ssh/id_ed25519_signing"
git config --global commit.gpgSign true
git config --global tag.gpgSign true

# 3. Vérification locale des signatures
echo "$(git config --global user.email) namespaces=\"git\" $(cat ~/.ssh/id_ed25519_signing.pub)" > ~/.config/git/allowed_signers
git config --global gpg.ssh.allowedSignersFile "$HOME/.config/git/allowed_signers"

# 4. Déclarer la clé sur GitHub (demande le scope admin:ssh_signing_key)
gh ssh-key add ~/.ssh/id_ed25519_signing.pub --type signing --title "$(scutil --get ComputerName) signing key"
```

Pour vérifier : `git log --show-signature -1` doit afficher `Good "git" signature`. Sur GitHub, les commits portent le badge **Verified**.

Attention : quand le ruleset exige des commits signés, GitHub vérifie **chaque commit de la PR**, même avec un squash merge. Une PR qui contient un seul commit non vérifié reste bloquée. La clé doit donc être déclarée sur GitHub **avant** d'activer cette règle, et en équipe, chaque coéquipier doit signer ses commits. Les commits créés par GitHub (squash, Dependabot, release-please) sont signés par la clé de GitHub.

## 6. Claude Code : pas d'attribution

`~/.claude/settings.json` doit contenir :

```json
"attribution": { "commit": "", "pr": "", "sessionUrl": false }
```

Ce réglage empêche Claude Code d'ajouter `Co-Authored-By` et « Generated with Claude Code ». C'est la vraie garantie : une consigne écrite seule ne suffit pas. `~/.claude/CLAUDE.md` rappelle aussi la règle à toutes les sessions. Modifie toujours ces fichiers en fusionnant avec leur contenu existant, jamais en l'écrasant.

## 7. Outils de hooks (selon les projets)

- Projets JS/TS : rien à installer globalement. Husky et commitlint s'installent avec `npm install`.
- Autres projets : le framework `pre-commit`.
  ```bash
  brew install pre-commit
  ```
  Demande à l'utilisateur avant de l'installer.

## 8. Où ranger les projets, et changer de branche sans casser l'app en cours

**Pas de dépôt Git dans un dossier synchronisé par iCloud.** Avec « Bureau et Documents » activé dans iCloud, tout ce qui est sous `~/Documents` ou `~/Desktop` est synchronisé. Quand Git réécrit beaucoup de fichiers d'un coup (changement de branche, rebase), iCloud crée des copies en conflit nommées `fichier 2.ext`, et peut à la longue abîmer `.git`. `doctor.sh` le signale quand il est lancé depuis un tel dossier. Conseille de déplacer les projets, par exemple dans `~/Developer` (la demande vient de l'utilisateur : ne déplace rien toi-même). Des copies « 2 » apparues : compare-les aux originaux (`cmp`), puis mets-les à la corbeille si ce sont d'anciennes versions.

**Pas de `git switch` pendant qu'un serveur de dev tourne sur le dossier.** Un `tauri dev`, `cargo watch` ou serveur Node recharge l'app à chaque changement de fichier : changer de branche la relance, parfois sur un code plus ancien qui ne connaît pas les données de la version actuelle. Pour travailler sur une autre branche, utilise un second dossier de travail :

```bash
git worktree add ../<repo>-<branche> <branche>     # ou un dossier temporaire
# … modifier, committer, pousser depuis ce dossier …
git worktree remove ../<repo>-<branche>
```

Une même branche ne peut être ouverte que dans un seul dossier à la fois. Les hooks husky ne sont pas installés dans un worktree neuf tant que `npm ci` n'y a pas été lancé.
