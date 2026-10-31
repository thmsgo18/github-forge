# Audit et mise aux normes d'un dépôt existant

`SKILL_DIR=~/.claude/skills/github-forge`.

## 1. Lancer l'audit

Depuis la racine du dépôt cloné :
```bash
$SKILL_DIR/scripts/audit-repo.py            # OWNER/REPO est déduit de origin, ou passe-le en argument
```

Le rapport est une checklist ✓ / ✗ / ⚠ en quatre parties : fichiers, hygiène locale, réglages GitHub, protection et sécurité. Il inclut aussi les traces d'IA dans l'historique.

## 2. Présenter le résultat

Résume en français, classé par gravité, en expliquant chaque point en une phrase :

1. **Critique** (sécurité) : secrets ou `.env` versionnés, `main` non protégée, push protection désactivée sur un dépôt public, traces d'IA dans l'historique. Si GitHub refuse la protection (dépôt privé gratuit), ce n'est pas une faute de l'utilisateur : propose l'offre qui manque ou la garde locale (`team.md` § « Sans protection GitHub »), que l'audit compte alors comme un avertissement.
2. **Important** (qualité) : pas de CI, pas de modèles de PR ou d'issue, fusion autre que squash, branches pas supprimées après fusion, pas de Dependabot.
3. **Finition** : pas de licence, pas de description ni de topics, pas de `.editorconfig`, branche par défaut `master`.

Puis propose un plan dans l'ordre ci-dessous et demande s'il faut tout appliquer ou seulement une partie.

## 3. Appliquer

L'ordre est le même que pour un setup (`repo-setup.md`), avec une différence : **les fichiers arrivent par une PR**, même si `main` n'est pas encore protégée. C'est la bonne habitude, et ça teste la CI avant de la rendre obligatoire.

1. **Une issue** (facultative pour ce travail de maintenance) : `Bring repository up to standards` dans la langue du dépôt, avec en case à cocher la liste de ce qui manque.
2. **Une branche** `chore/<N>-repo-standards` (ou `chore/repo-standards` sans issue) contenant les fichiers manquants (repo-setup.md § 4 et § 5), puis une PR, la CI au vert, et la fusion.
3. **Les réglages** : `configure-repo.sh OWNER/REPO [--releases]`.
4. **La protection** : `protect-main.sh OWNER/REPO solo|team "<nom de chaque job de CI>" "PR title"`, une fois la CI sur `main`. En cas de refus 403, garde locale de `main` par une PR (`team.md`).
5. **Un nouvel audit** : tout doit être en ✓.

### Secrets versionnés

Retirer le fichier du dépôt ne suffit pas, car il reste dans l'historique. **Commence par révoquer le secret** chez le fournisseur (nouvelle clé API, nouveau mot de passe) : c'est la seule vraie protection. Ensuite :

```bash
git rm --cached .env && echo ".env" >> .gitignore
git commit -m "chore: stop tracking .env"
```

Nettoyer l'historique est optionnel une fois le secret révoqué. La procédure est la même que pour les traces d'IA, ci-dessous.

### Branche par défaut `master` → `main`

```bash
gh api -X POST repos/OWNER/REPO/branches/master/rename -f new_name=main
git branch -m master main
git fetch origin
git branch -u origin/main main
git remote set-head origin -a
```

GitHub redirige automatiquement les anciens liens. Préviens les coéquipiers : chacun doit lancer les trois dernières commandes de son côté.

### Fichiers Claude versionnés

S'ils sont suivis (`CLAUDE.md`, `.claude/`) :
```bash
git rm -r --cached CLAUDE.md .claude 2>/dev/null
git commit -m "chore: stop tracking local tool configuration"
```

Les fichiers restent sur le disque, mais ne sont plus publiés. Le message de commit reste neutre.

## 4. Traces d'IA dans l'historique

Ce sont des commits passés qui contiennent `Co-Authored-By: Claude` ou « Generated with Claude Code ». C'est à cause d'eux que GitHub affiche Claude parmi les contributeurs. La seule façon de les retirer est de **réécrire l'historique**. Explique clairement les conséquences avant de proposer quoi que ce soit :

- Tous les commits concernés **changent d'identifiant** (SHA), ainsi que tous ceux qui suivent.
- Il faut un **force-push sur `main`**, donc désactiver temporairement le ruleset.
- Chaque clone existant (coéquipiers, autres machines) devra être recloné.
- Les anciens commits réécrits perdent leur signature. Les nouveaux restent signés.
- La liste des contributeurs GitHub peut mettre quelques heures à se mettre à jour.

Recommandation : sur un dépôt **perso et solo**, c'est faisable sans risque si on suit la procédure. Sur un dépôt **d'équipe**, il faut l'accord de tous et choisir un moment où personne ne travaille. Sinon, mieux vaut laisser l'historique tel quel.

Procédure, avec l'accord explicite de l'utilisateur à chaque étape :

```bash
# 0. Outil
command -v git-filter-repo || echo "proposer : brew install git-filter-repo"

# 1. Sauvegarde complète hors du projet
git clone --mirror https://github.com/OWNER/REPO.git ~/repo-backups/REPO-$(date +%Y%m%d).git

# 2. Réécriture dans un clone neuf (filter-repo l'exige)
cd "$(mktemp -d)" && git clone https://github.com/OWNER/REPO.git && cd REPO
git filter-repo --message-callback '
import re
message = re.sub(rb"(?im)^\s*co-authored-by:.*(claude|anthropic).*\n?", b"", message)
message = re.sub(rb"(?im)^.*generated with \[?claude.*\n?", b"", message)
message = re.sub(rb"(?m)^\s*\xf0\x9f\xa4\x96.*\n?", b"", message)
return message.rstrip() + b"\n"
'
$SKILL_DIR/scripts/check-no-ai-trace.py --all       # doit être vide

# 3. Publication : désactive le ruleset, force-push, réactive
RID=$(gh api repos/OWNER/REPO/rulesets --jq '.[] | select(.name=="Protect main") | .id')
gh api -X PUT repos/OWNER/REPO/rulesets/$RID -f enforcement=disabled
git remote add origin https://github.com/OWNER/REPO.git
git push --force --all && git push --force --tags
gh api -X PUT repos/OWNER/REPO/rulesets/$RID -f enforcement=active
```

Ensuite, l'utilisateur reclone le dépôt à son emplacement habituel. Pour un dépôt **jamais publié**, il suffit de lancer l'étape 2 directement dans le dépôt local, après une copie de sauvegarde du dossier.

### Variante : repartir de zéro dans un dépôt neuf

Quand l'historique n'a pas de valeur pour l'équipe (projet jeune, branches qui ont divergé, `main` en retard sur une branche de travail), un dépôt neuf est plus propre qu'un force-push. Un force-push laisse les anciens commits visibles dans les pages des PR déjà ouvertes, qu'on ne peut pas supprimer. Un dépôt neuf repart sans traces d'IA, sans fichiers locaux versionnés, avec une seule branche et des numéros d'issue et de PR à partir de 1. Accord explicite de toute l'équipe avant de commencer.

```bash
# 1. Chaque coéquipier pousse ou met de côté son travail local. Sauvegarde complète, hors du dépôt :
git bundle create ../REPO-historique-$(date +%Y-%m-%d).bundle --all && git bundle verify ../REPO-historique-*.bundle

# 2. Libérer le nom : renommer puis archiver l'ancien dépôt (lecture seule, privé)
gh repo rename REPO-archive -R OWNER/REPO --yes && gh repo archive OWNER/REPO-archive --yes

# 3. Nouveau dépôt vide, même nom donc même URL
gh repo create OWNER/REPO --private --description "<description>"

# 4. Commit initial : le contenu de la branche à garder, sans parent
#    (switch --orphan vide le dossier de travail : on remet aussitôt le contenu)
git switch --orphan depart && git checkout <branche-a-garder> -- .
git rm -r -q --cached .claude CLAUDE.md 2>/dev/null; printf '\n.claude/\nCLAUDE.md\n' >> .gitignore && git add .gitignore
$SKILL_DIR/scripts/check-no-ai-trace.py --head     # le commit doit être propre
git commit -m "chore: point de départ de REPO" -m "Co-authored-by: Prénom Nom <ID+pseudo@users.noreply.github.com>"
git branch -D main <autres-branches> && git branch -m depart main && git push -u origin main
git reflog expire --expire=now --all && git gc --prune=now    # plus aucun ancien commit à republier par erreur

# 5. Réglages puis fichiers pro par une première PR, relue par l'équipe
$SKILL_DIR/scripts/configure-repo.sh OWNER/REPO
```

- Le trailer `Co-authored-by` d'un coéquipier humain est permis : il garde son travail crédité alors que l'ancien historique disparaît. Son adresse noreply se calcule avec `gh api users/<pseudo> --jq .id`.
- Les membres d'une organisation dont la permission par défaut est `write` ont accès au nouveau dépôt sans invitation.
- Chaque coéquipier **reclone** le dépôt dans un nouveau dossier. L'ancien clone pointe sur la même URL : il ne doit plus rien pousser, sous peine de republier l'ancien historique.

## 5. Auditer plusieurs dépôts

Pour faire le tour des dépôts de l'utilisateur :
```bash
LOGIN=$(gh api user --jq .login)
gh repo list "$LOGIN" --limit 100 --json name,visibility,isArchived,pushedAt \
  --jq '.[] | select(.isArchived|not) | [.name,.visibility,.pushedAt] | @tsv'
```

Pour repérer vite les dépôts qui contiennent des traces d'IA, sans les cloner :
```bash
for r in $(gh repo list "$LOGIN" --limit 100 --json name --jq '.[].name'); do
  n=$(gh api "repos/$LOGIN/$r/commits?per_page=100" --jq '[.[] | select(.commit.message | test("(?i)co-authored-by:.*(claude|anthropic)|generated with \\[?claude"))] | length' 2>/dev/null)
  [ "${n:-0}" -gt 0 ] && echo "$r : $n commit(s) récents avec trace"
done
```

Ce scan ne regarde que les 100 derniers commits de chaque dépôt. Présente un tableau des dépôts, puis laisse l'utilisateur choisir lesquels mettre aux normes : un dépôt par PR, en commençant par ceux qui comptent pour son portfolio.
