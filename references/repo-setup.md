# Setup d'un dépôt

Pour un nouveau projet, ou un dossier existant pas encore sur GitHub. Si le dépôt est **déjà sur GitHub**, suis plutôt `audit.md`.

L'ordre des étapes compte. Les fichiers et la CI doivent être sur `main` **avant** de poser la protection, sinon la protection exigerait des vérifications qui n'existent pas encore.

`SKILL_DIR=~/.claude/skills/github-forge` dans tout ce guide.

## Sommaire
1. Recueillir les infos
2. Détecter la stack
3. Initialiser le dépôt local
4. Ajouter les fichiers pro
5. Installer les hooks
6. Vérifier avant le premier commit
7. Premier commit et création sur GitHub
8. Réglages GitHub
9. Releases (si choisies)
10. Protection de main
11. Vérification finale et récap

---

## 1. Recueillir les infos

Pose toutes les questions **en une fois** (avec l'outil de questions s'il est disponible), avec une valeur par défaut pour chacune :

| Question | Défaut | Note pour l'utilisateur |
|---|---|---|
| Nom du dépôt | nom du dossier en kebab-case | Visible dans l'URL : court, en anglais, en minuscules |
| Description (une ligne, en anglais) | à proposer d'après le code | S'affiche en haut du dépôt et dans les recherches |
| Visibilité | **public** | Public = vitrine pour le portfolio. En privé, la protection de `main` et le blocage des secrets demandent une offre payante : GitHub Pro pour un compte personnel (gratuit avec le Student Pack), GitHub Team pour une organisation (le Student Pack ne couvre pas les organisations). Sans elle, on pose la garde locale de `main` (`team.md`) |
| Solo ou équipe | solo | En équipe, il faut les pseudos GitHub des coéquipiers |
| Licence | MIT | MIT = « faites-en ce que vous voulez ». Apache-2.0 = idem avec une protection sur les brevets. GPL-3.0 = les dérivés doivent rester libres. Aucune = tous droits réservés |
| Nom dans la licence | demande-le (ne le devine pas d'après le pseudo) | Le titulaire des droits |
| Releases automatiques | oui pour une app ou une bibliothèque, non pour un projet de cours ou un site | Voir `releases.md` |
| Topics GitHub | à proposer d'après la stack | Des mots-clés (`typescript`, `react`…) qui rendent le dépôt trouvable |

## 2. Détecter la stack

| Fichier présent | Stack | Workflow CI | `.gitignore` GitHub | Écosystème Dependabot | release-type |
|---|---|---|---|---|---|
| `package.json` | Node / JS / TS | `ci-node.yml` | `Node` | `npm` | `node` |
| `pyproject.toml` + `uv.lock` | Python (uv) | `ci-python-uv.yml` | `Python` | `uv` | `python` |
| `pyproject.toml` / `requirements.txt` | Python (pip) | `ci-python.yml` | `Python` | `pip` | `python` |
| `pom.xml` | Java Maven | `ci-java-maven.yml` | `Java` + `Maven` | `maven` | `maven` |
| `build.gradle(.kts)` | Java/Kotlin Gradle | `ci-java-gradle.yml` | `Java` + `Gradle` | `gradle` | `simple` |
| `*.tex` | LaTeX | `ci-latex.yml` | `TeX` | — | `simple` |
| `Cargo.toml` | Rust | `ci-rust.yml` | `Rust` | `cargo` | `rust` |
| `src-tauri/tauri.conf.json` | Tauri (Node + Rust) | `ci-tauri.yml` | `Node` + `Rust` | `npm` + `cargo` | `node` |
| autre | générique | `ci-generic.yml` | à composer | — | `simple` |

Pour Node, le lockfile indique le gestionnaire de paquets : `package-lock.json` → npm, `pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn. Adapte les commandes du workflow en conséquence. Projet vide : propose la stack prévue, ou pars sur le générique et adapte plus tard.

**Code dans un sous-dossier** (`app/`, `frontend/`, un `package.json` qui n'est pas à la racine) : repère-le avant de copier quoi que ce soit, il change plusieurs fichiers.

- CI : `defaults.run.working-directory: app` et `cache-dependency-path: app/package-lock.json` (voir `ci-tauri.yml`).
- Dependabot : `directory: "/app"` pour npm, `"/app/src-tauri"` pour Cargo ; le bloc `github-actions` garde `"/"`.
- Hooks husky : le dossier `.husky/` vit à côté du `package.json` (§ 5, « Code dans un sous-dossier »).

## 3. Initialiser le dépôt local

```bash
git init                         # crée main directement (init.defaultBranch=main)
git branch --show-current        # vérifie : main
```

Si le dépôt existe déjà sur `master`, renomme la branche : `git branch -m master main`.

S'il a déjà un historique, cherche les traces d'IA **avant la première publication** :
```bash
$SKILL_DIR/scripts/check-no-ai-trace.py --all
```
Si le script en trouve, rien n'est encore publié : c'est le seul moment où réécrire l'historique ne casse rien pour personne. Propose le nettoyage décrit dans `audit.md` (§ « Traces d'IA dans l'historique »).

## 4. Ajouter les fichiers pro

Copie depuis `$SKILL_DIR/assets/`, puis remplace les `{{PLACEHOLDERS}}`. Ne copie jamais par-dessus un fichier qui existe déjà sans le lire : fusionne plutôt les deux.

| Fichier dans le projet | Source | À adapter |
|---|---|---|
| `.gitignore` | `gh api gitignore/templates/<Nom> --jq .source`, plus les lignes propres au projet | Combine plusieurs modèles si besoin (Java + Maven) |
| `.editorconfig` | `assets/templates/editorconfig` | Indentation selon la stack |
| `.gitattributes` | `assets/templates/gitattributes` | — |
| `LICENSE` | `gh api licenses/<mit\|apache-2.0\|gpl-3.0> --jq .body` | Remplace `[year]` et `[fullname]` (ou `<year>` / `<name of author>` selon la licence) |
| `README.md` | Utilise le skill **readme-forge** s'il est disponible, sinon `assets/templates/README.md` | Badge CI avec OWNER/REPO |
| `CONTRIBUTING.md` | `assets/templates/CONTRIBUTING.md`, ou `assets/templates/fr/CONTRIBUTING.md` pour un dépôt en français | Tous les `{{…}}`. `{{TEAM_RULE}}` : vide en solo. En équipe : ` At least one approving review from another contributor is required, and all review conversations must be resolved.` (FR : ` L'autre relit et approuve la PR, et les discussions sont résolues avant la fusion.`) `{{MAIN_RULE}}` : si `main` est protégée, « Direct pushes to main are blocked. » ; sans protection GitHub, « Never commit or push directly to main: local Git hooks refuse it. Don't bypass them with --no-verify. » (FR : « Jamais de commit ni de push direct sur main : les hooks Git locaux le refusent. On ne les contourne pas avec --no-verify. »). Mets main et --no-verify entre accents graves dans le fichier final. `{{HOOKS_INSTALL_LINE}}` : `# Git hooks install automatically with npm install` (JS) ou `pre-commit install` |
| `.github/PULL_REQUEST_TEMPLATE.md` | `assets/templates/github/PULL_REQUEST_TEMPLATE.md` (ou `assets/templates/fr/github/…`) | — |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | `assets/templates/github/ISSUE_TEMPLATE/bug_report.yml` (ou `assets/templates/fr/github/…`) | — |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | `assets/templates/github/ISSUE_TEMPLATE/feature_request.yml` (ou `assets/templates/fr/github/…`) | — |
| `.github/ISSUE_TEMPLATE/config.yml` | `assets/templates/github/ISSUE_TEMPLATE/config.yml` | — |
| `.github/CODEOWNERS` | `assets/templates/github/CODEOWNERS` | `@<pseudo>`, plus les coéquipiers en mode équipe |
| `.github/dependabot.yml` | `assets/templates/github/dependabot.yml` | Garde le ou les blocs des écosystèmes détectés (Tauri : `npm` et `cargo`), avec le bon `directory`. Le bloc `github-actions` est toujours présent |
| `.github/workflows/ci.yml` | `assets/workflows/ci-<stack>.yml` | Commandes réelles du projet. Un job unique s'appelle **`name: CI`** ; s'il y en a plusieurs (`ci-tauri.yml` : interface et Rust), note leurs `name:` exacts, ce sont eux qu'on passe à `protect-main.sh` |
| `.github/workflows/pr-title.yml` | `assets/workflows/pr-title.yml` | Rien à changer. Le job s'appelle **`PR title`** |
| `release-please-config.json`, `.release-please-manifest.json`, `.github/workflows/release.yml` | `assets/release/…` et `assets/workflows/release.yml` | Seulement si les releases sont choisies. `release-type` d'après la stack (§ 2). Version du projet (`package.json`…) à `0.0.0` |

Vérifie ensuite qu'il ne reste aucun placeholder : `grep -rnE '\{\{[A-Z_0-9]+\}\}' --exclude-dir=node_modules .`. Les `${{ … }}` des workflows sont des expressions GitHub Actions : il faut les laisser.

### Règles pour la CI

- Le nom des jobs (`CI`, `PR title`, ou les `name:` de chaque job) est ce que la protection de `main` attend : **ne les renomme pas** une fois la protection posée, sinon la fusion reste bloquée en attente d'un check qui n'existe plus.
- La CI doit tourner sur **toutes** les PR, sans filtre `paths:`. Sinon, une PR qui ne touche que la doc resterait bloquée en attente d'une vérification qui ne démarre jamais.
- N'appelle que des scripts qui existent. Par exemple `npm run lint --if-present` saute proprement s'il n'y a pas de linter.
- S'il n'y a encore aucun test, la CI doit quand même passer : build et lint seuls. Propose ensuite d'ajouter des tests dans une issue dédiée.

## 5. Installer les hooks

Ils vérifient le format et le message de commit **avant** que le commit soit créé.

### JS / TS : husky + lint-staged + commitlint

```bash
npm install -D husky lint-staged @commitlint/cli @commitlint/config-conventional
npx husky init                                   # ajoute le script "prepare" et crée .husky/
cp $SKILL_DIR/assets/hooks/commitlint.config.mjs .
printf 'npx --no -- commitlint --edit "$1"\n' > .husky/commit-msg
printf 'npx lint-staged\n' > .husky/pre-commit
```

Ajoute ensuite la config lint-staged dans `package.json`. N'utilise que les outils déjà présents dans le projet :

```json
"lint-staged": {
  "*.{js,jsx,ts,tsx,mjs,cjs}": ["eslint --fix", "prettier --write"],
  "*.{json,md,css,scss,yml,yaml,html}": "prettier --write"
}
```

**Code dans un sous-dossier** (`app/package.json`) : husky doit savoir où est la racine Git, et le message de commit est donné relatif à cette racine. Dans `app/` :

```bash
npm install -D husky @commitlint/cli @commitlint/config-conventional
npm pkg set scripts.prepare="cd .. && husky app/.husky"
mkdir -p .husky && cp $SKILL_DIR/assets/hooks/commitlint.config.mjs .
cp $SKILL_DIR/assets/hooks/husky-subdir-commit-msg .husky/commit-msg   # remplace « app » si le dossier s'appelle autrement
npm run prepare
```

Les hooks tournent depuis la racine du dépôt : un hook qui lance une commande npm commence par `cd app`.

Avec Prettier, ajoute aussi les scripts `"lint": "prettier --check ."` et `"format": "prettier --write ."`. Ajoute un `.prettierignore` contenant `CHANGELOG.md` et `package-lock.json` : ces fichiers générés ne doivent pas faire échouer la CI. Lance `npx prettier --write .` une fois avant le premier commit.

S'il n'y a ni ESLint ni Prettier, propose d'ajouter Prettier (`npm i -D prettier`), le formateur standard. Si l'utilisateur refuse, mets `"lint-staged": {}` et laisse seulement le hook commit-msg utile, en remplaçant `.husky/pre-commit` par `npm test`, ou en le supprimant si les tests sont lents. Les coéquipiers récupèrent les hooks automatiquement avec `npm install`, grâce au script `prepare`.

### Autres stacks : pre-commit

```bash
command -v pre-commit || echo "pre-commit absent : proposer brew install pre-commit"
cp $SKILL_DIR/assets/hooks/pre-commit-config.yaml .pre-commit-config.yaml
# Python : décommente le bloc ruff dans le fichier
pre-commit autoupdate      # met les versions des hooks à jour
pre-commit install         # installe pre-commit ET commit-msg (default_install_hook_types)
pre-commit run --all-files # premier passage : corrige les espaces et les fins de fichier
```

Les coéquipiers lancent `pre-commit install` une fois après le clone. C'est écrit dans `CONTRIBUTING.md`.

**Test du hook** : `git commit --allow-empty -m "bad message"` doit être **refusé**. Annule ensuite avec `git reset --soft HEAD~1` si jamais il est passé.

## 6. Vérifier avant le premier commit

C'est le moment où une erreur coûte le plus cher : un secret publié dans un dépôt public est compromis en quelques minutes.

```bash
git add -A && git status --short                    # ce qui partirait (git reset pour tout retirer de l'index)
git ls-files --others --exclude-standard | grep -Ei '\.env|secret|credential|\.pem|\.key|id_rsa' || true
find . -size +5M -not -path './.git/*' -not -path './node_modules/*' | head   # gros fichiers
```

Montre la liste à l'utilisateur. S'il y a un `.env`, des clés, des données personnelles ou des fichiers de plus de 5 Mo, ajoute-les au `.gitignore` avant le commit.

## 7. Premier commit et création sur GitHub

```bash
git add -A
git commit -m "chore: initial project setup"
```

Si le projet contenait déjà du code et que les fichiers pro sont un ajout, fais deux commits : `feat: initial implementation` pour le code, puis `chore: add project tooling and community files`.

Demande confirmation, puis crée le dépôt et pousse :

```bash
gh repo create <name> --public --source=. --remote=origin --push \
  --description "<one-line description>"
gh repo edit --add-topic typescript --add-topic cli   # topics proposés
```

Le dépôt existe déjà sur GitHub mais il est vide ? Fais `git remote add origin https://github.com/OWNER/REPO.git` puis `git push`.

## 8. Réglages GitHub

```bash
$SKILL_DIR/scripts/configure-repo.sh OWNER/REPO            # ajoute --releases si les releases sont choisies
```

Le script règle :
- la fusion en **squash seul**, avec le titre de la PR comme message de commit et le corps de la PR comme description ;
- la suppression automatique des branches après fusion ;
- l'auto-merge et le bouton « Update branch » ;
- sur un dépôt public, le scan des secrets et le **blocage des push qui en contiennent** ;
- les alertes Dependabot et les correctifs de sécurité automatiques ;
- des permissions des workflows en lecture seule par défaut ;
- avec `--releases`, l'autorisation pour les Actions de créer des PR.

Il affiche un récap. Signale à l'utilisateur toute ligne en ⚠.

## 9. Releases (si choisies)

Les fichiers ont été ajoutés à l'étape 4 et `configure-repo.sh --releases` a autorisé les Actions à créer des PR (étape 8). Il reste à proposer à l'utilisateur de créer le token `RELEASE_PLEASE_TOKEN`, sans quoi la CI ne tournera pas sur la PR de release (`releases.md` § « Le piège des checks »). La première release sera `0.1.0`.

## 10. Protection de main

Attends que `ci.yml` et `pr-title.yml` soient sur `main`. Les noms de checks n'existent pour GitHub qu'une fois que les workflows ont tourné au moins une fois.

```bash
$SKILL_DIR/scripts/protect-main.sh OWNER/REPO solo "CI" "PR title"
# en équipe :
$SKILL_DIR/scripts/protect-main.sh OWNER/REPO team "CI" "PR title"
```

**Commits signés** : en solo, la règle est activée par défaut. Elle bloque toute PR qui contient un commit non vérifié. Vérifie d'abord avec `doctor.sh` que la clé est déclarée sur GitHub. Sinon, ajoute `--no-signatures` et relance plus tard sans l'option. En équipe, la règle est désactivée par défaut. Ajoute `--signatures` seulement si chaque coéquipier signe ses commits.

Sans CI (si l'utilisateur l'a explicitement refusée), n'indique aucun check. En privé sans offre payante, le script échoue avec une erreur 403 et dit quelle offre manque : GitHub Pro pour un compte personnel (gratuit avec le Student Pack), GitHub Team pour une organisation. Si l'utilisateur ne veut ni payer ni rendre le dépôt public, pose la garde locale de `main` (`team.md` § « Sans protection GitHub »).

## 11. Vérification finale et récap

```bash
$SKILL_DIR/scripts/audit-repo.py OWNER/REPO
```

Tout doit être en ✓. Corrige les ✗, puis donne le récap à l'utilisateur :
- l'URL du dépôt ;
- ce qui a été mis en place, en une ligne par élément (protection, CI, sécurité, releases) ;
- ce qu'il doit faire lui-même, par exemple créer le token release-please (voir `releases.md`) ;
- la suite : « Pour ta première tâche, dis-moi ce que tu veux faire : je crée l'issue et la branche. »
