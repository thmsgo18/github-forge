# Conventions

Le référentiel complet des règles d'écriture. Tout ce qui est écrit dans Git ou sur GitHub est **dans la langue du dépôt** : celle de ses derniers commits (`git log -20 --format=%s`), l'anglais pour un dépôt neuf sauf si l'utilisateur préfère le français. Les types (`feat`, `fix`…) et les mots-clés (`Closes #12`, `BREAKING CHANGE:`) restent en anglais dans tous les cas. Les exemples ci-dessous sont en anglais ; un dépôt en français suit les mêmes règles avec des phrases françaises (`feat(auth): ajouter la connexion Google`).

## Sommaire
1. Types de changement
2. Branches
3. Commits
4. Pull requests
5. Issues
6. Aucune trace d'IA

---

## 1. Types de changement

Le même vocabulaire sert pour les branches, les commits et les titres de PR. Choisis le type d'après **l'effet principal** du changement.

| Type | Quand l'utiliser | Effet sur la version |
|---|---|---|
| `feat` | Nouvelle capacité visible par l'utilisateur ou par l'API | minor (1.**2**.0) |
| `fix` | Correction d'un bug | patch (1.1.**1**) |
| `perf` | Amélioration de performance, sans changement de comportement | patch |
| `refactor` | Restructuration du code sans changement de comportement | aucun |
| `docs` | Documentation seulement (README, commentaires, docs/) | aucun |
| `test` | Ajout ou correction de tests seulement | aucun |
| `style` | Formatage pur (espaces, points-virgules), sans effet sur la logique | aucun |
| `build` | Système de build, dépendances, packaging | aucun |
| `ci` | Workflows GitHub Actions, config de la CI | aucun |
| `chore` | Maintenance qui ne touche ni au code source ni aux tests (outillage, config) | aucun |
| `revert` | Annulation d'un commit précédent | selon le commit annulé |

**Changement cassant** : quand un utilisateur du code doit modifier son propre code (API supprimée ou renommée, format changé), ajoute `!` après le type ou le scope. Ajoute aussi un footer `BREAKING CHANGE: …` qui explique la migration. Effet sur la version : **major** (**2**.0.0). Avant la 1.0.0, un changement cassant fait seulement monter le minor.

**Hésitation fréquente** : un bug corrigé en réécrivant un module est un `fix`, car c'est l'effet qui compte. Une nouvelle option ajoutée à une fonction existante est un `feat`. Mettre à jour une dépendance pour corriger une faille est un `fix(deps)`. Une mise à jour de routine est un `build(deps)` ou un `chore(deps)`. Un bug dans l'outillage (CI, config de release, scripts de dev) n'est pas un `fix` : utilise `ci`, `build` ou `chore`. Un `fix` déclenche une release et apparaît dans le CHANGELOG lu par les utilisateurs.

## 2. Branches

Format : **`<type>/<issue>-<slug>`**

- `type` : un des types ci-dessus.
- `issue` : le numéro de l'issue, sans `#`.
- `slug` : 2 à 5 mots dans la langue du dépôt, sans accents, en minuscules, séparés par des tirets, qui résument la tâche.

Une tâche de maintenance sans issue (`chore`, `docs`, `ci`, `build`) prend la forme `<type>/<slug>`, par exemple `chore/repo-setup`. Une fonctionnalité ou un bug a toujours son issue.

```
feat/12-google-sign-in
fix/27-negative-cart-quantity
docs/31-install-instructions
refactor/40-extract-user-service
ci/44-cache-npm-dependencies
```

À éviter : `thomas-branch`, `fix`, `feat/GoogleSignIn`, `feature/12_google_sign_in`, `test2`.

Une branche correspond à une issue et à une PR. Elle vit quelques heures à quelques jours : au-delà, découpe la tâche. Les branches créées par des robots (`dependabot/…`, `release-please--…`) suivent leur propre format : n'y touche pas.

## 3. Commits

### Format

```
<type>(<scope>): <description>

<corps optionnel : le POURQUOI, lignes de 72 caractères max>

<footers optionnels : BREAKING CHANGE: …, Refs #12>
```

- **scope** (facultatif) : la zone touchée, en un mot (`auth`, `cart`, `api`, `ui`, `deps`, `readme`, `ci`). Garde les mêmes scopes d'un commit à l'autre dans un projet.
- **description** : à l'impératif, en commençant par une minuscule, sans point final. Ligne d'en-tête de 72 caractères maximum. Elle doit compléter la phrase « If applied, this commit will… ». En français, à l'infinitif : `fix(panier): empêcher les quantités négatives`.
- **corps** : explique *pourquoi* le changement est fait, et *quoi* seulement si ce n'est pas évident. Le diff montre déjà le *comment*.

### Exemples

```
feat(auth): add Google sign-in
fix(cart): prevent negative quantities
docs(readme): add installation steps
refactor(api): extract user service from controller
test(cart): cover empty cart checkout
build(deps): bump express from 4.21.0 to 5.1.0
ci: cache npm dependencies
perf(search): debounce query input
feat(api)!: remove v1 endpoints

BREAKING CHANGE: /v1/* routes are gone. Use /v2/* instead.
```

À éviter : `update`, `fix bug`, `WIP`, `Added Google Sign-In.`, `feat: Add google sign in and fix cart and update readme` (trois changements dans un seul commit).

### Quand committer

Committe à **chaque étape cohérente qui fonctionne** : la fonction marche et les tests passent. Chaque commit doit pouvoir être compris et annulé seul. Ne mélange pas un refactor et une nouvelle fonctionnalité dans le même commit.

Sur une branche, les commits intermédiaires peuvent être petits, puisque le squash les fusionnera en un seul. Ils respectent quand même la convention : les hooks la vérifient, et c'est une bonne habitude.

Avant chaque commit :
```bash
git status                 # que va-t-on committer ?
git add <fichiers précis>  # évite `git add .` à l'aveugle : pas de fichiers parasites
git diff --staged          # relis ce qui part
git commit -m "feat(cart): add quantity selector"
```

## 4. Pull requests

### Titre

Le **titre de la PR est un Conventional Commit**. Avec le squash merge, c'est lui qui devient le message du commit dans `main`, et GitHub ajoute ` (#13)` à la fin. La CI (`pr-title.yml`) le vérifie.

Si la PR contient plusieurs commits de types différents, choisis le type de l'effet principal. Si elle fait vraiment deux choses distinctes, découpe-la en deux PR.

### Corps

Remplis le modèle `.github/PULL_REQUEST_TEMPLATE.md` dans la langue du dépôt, de façon concise :

```markdown
## What
Adds a "Sign in with Google" button on the login page using OAuth 2.0.

## Why
Most users already have a Google account; this removes the signup friction.

Closes #12

## How to test
1. `npm run dev`
2. Open /login and click "Sign in with Google"
3. You land on /dashboard, signed in

## Checklist
- [x] Tests added or updated
- [x] Docs updated if needed
- [ ] Breaking change
```

`Closes #12` (ou `Fixes #12`) ferme automatiquement l'issue à la fusion. Mets un mot-clé par issue : `Closes #12, closes #14`.

### Bonnes pratiques

- **Petite PR** : idéalement moins de 400 lignes modifiées. Une PR plus grosse est relue moins bien.
- **Draft PR** (`--draft`) pour montrer un travail en cours ou demander un avis tôt.
- **Assignée à soi** (`--assignee @me`).
- Relis ton propre diff sur GitHub avant de demander une relecture.

## 5. Issues

- **Titre** : clair, dans la langue du dépôt, sans préfixe de type. Une fonctionnalité se décrit par l'action (`Add Google sign-in`), un bug par le symptôme (`Cart accepts negative quantities`).
- **Corps** : suis la structure des formulaires du dépôt.
  - Feature : *Problem*, *Proposed solution*, *Acceptance criteria* (une liste de cases à cocher).
  - Bug : *What happened*, *Steps to reproduce*, *Expected behavior*, *Environment*.
- **Labels** : `bug`, `enhancement` ou `documentation` (ils existent par défaut sur GitHub).
- **Assignation** : à soi au moment où on commence (`gh issue edit 12 --add-assignee @me`).

Pour créer une issue en ligne de commande :

```bash
URL=$(gh issue create --title "Add Google sign-in" --label enhancement --assignee @me --body "$(cat <<'EOF'
### Problem
Users must create a password to sign up, which causes drop-off.

### Proposed solution
Offer "Sign in with Google" using OAuth 2.0.

### Acceptance criteria
- [ ] A Google button is shown on /login
- [ ] A new user is created on first Google sign-in
- [ ] Existing users are matched by email
EOF
)")
N=${URL##*/}   # numéro de l'issue, pour nommer la branche
```

## 6. Aucune trace d'IA

L'interdiction couvre tout ce qui est publié : messages de commit, trailers (`Co-Authored-By`), titres et corps de PR et d'issues, commentaires, reviews, noms de branches, notes de release, CHANGELOG, et commentaires de code ajoutés pour l'occasion.

Pas de mention de Claude, d'Anthropic, ni d'expressions comme « AI-generated » ou « generated with/by … », et pas d'emoji 🤖.

Vérifie avant de publier :

```bash
SKILL_DIR=~/.claude/skills/github-forge
$SKILL_DIR/scripts/check-no-ai-trace.py                         # commits de la branche absents de origin/main
printf '%s\n\n%s' "$TITLE" "$BODY" | $SKILL_DIR/scripts/check-no-ai-trace.py --stdin   # titre et corps de PR
```

Si le projet lui-même porte sur Claude ou l'IA (par exemple une app qui appelle l'API Claude), parler du *sujet* du projet est légitime : `feat(chat): stream Claude API responses`. Ce qui est interdit, c'est de signaler que l'IA a *écrit* le code. Le script signale les mots-clés : à toi de juger, et en cas de doute, demande à l'utilisateur.
