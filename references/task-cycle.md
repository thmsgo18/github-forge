# Cycle d'une tâche

De l'idée jusqu'au code fusionné dans `main`. Les conventions d'écriture sont dans `conventions.md`. `SKILL_DIR=~/.claude/skills/github-forge`.

## Sommaire
1. Démarrer : issue et branche
2. Travailler : commits
3. Rester à jour avec main
4. Ouvrir la PR
5. CI et relecture
6. Fusionner et nettoyer

---

## 1. Démarrer : issue et branche

**Point de départ propre** :
```bash
git status -sb
```
Si des fichiers sont modifiés, demande ce qu'on en fait. Soit ils font partie de la nouvelle tâche : ils suivront tout seuls sur la nouvelle branche. Soit ils appartiennent à autre chose : commit sur leur propre branche, ou `git stash push -m "description"`.

**Trouver ou créer l'issue** :
```bash
gh issue list --state open --search "<mots-clés>"
```
- Une issue existe : `gh issue edit <N> --add-assignee @me`.
- Sinon, crée-la (format dans `conventions.md` § 5) après avoir vérifié le titre et le corps avec `check-no-ai-trace.py --stdin`. Récupère le numéro depuis l'URL renvoyée : `URL=$(gh issue create …)` puis `N=${URL##*/}`. `gh issue list --search` ne voit une issue toute neuve qu'après quelques secondes.

**Créer la branche depuis un `main` à jour** :
```bash
git switch main
git pull                                   # ff-only : s'il échoue, voir troubleshooting.md « Commits sur main par erreur »
git switch -c <type>/<N>-<slug>
```

## 2. Travailler : commits

Committe à chaque étape cohérente qui fonctionne. Avant chaque commit, lance les tests du projet s'ils sont rapides :

```bash
git status
git add <fichiers>
git diff --staged --stat
git commit -m "<type>(<scope>): <description>"
```

Les hooks vérifient le format et le message. S'ils refusent, corrige la cause (format du code, message du commit) et recommence. Pas de `--no-verify`.

**Pousser régulièrement** sert de sauvegarde et rend le travail visible. Au premier push de la branche, demande confirmation. Ensuite, pousser sur **sa propre** branche fait partie du flux normal :
```bash
$SKILL_DIR/scripts/check-no-ai-trace.py && git push
```

## 3. Rester à jour avec main

Si `main` a avancé pendant qu'on travaille (d'autres PR fusionnées) :

```bash
git fetch origin
git merge origin/main
```

On fusionne plutôt que de faire un rebase, pour deux raisons. D'abord, le squash final efface de toute façon l'historique de la branche. Ensuite, un merge ne réécrit jamais ce qui a déjà été poussé, donc jamais besoin de force-push. En cas de conflit, suis `troubleshooting.md` § « Conflit ».

Fais-le au moins avant d'ouvrir la PR, et chaque fois que GitHub signale que la branche est en retard.

## 4. Ouvrir la PR

**Vérifications préalables** :
```bash
<commande de test du projet>                        # npm test, pytest, mvn verify…
git fetch origin && git merge origin/main           # à jour
git diff origin/main...HEAD --stat                  # ce que contient la PR
$SKILL_DIR/scripts/check-no-ai-trace.py             # commits propres
```

**Préparer le titre et le corps** (dans la langue du dépôt) :
- Titre : un Conventional Commit qui résume l'effet de toute la PR.
- Corps : le modèle `.github/PULL_REQUEST_TEMPLATE.md` rempli, avec `Closes #<N>`.

```bash
TITLE="feat(auth): add Google sign-in"
BODY_FILE=$(mktemp)
cat > "$BODY_FILE" <<'EOF'
## What
...
## Why
...

Closes #12

## How to test
1. ...

## Checklist
- [x] Tests added or updated
- [ ] Docs updated if needed
- [ ] Breaking change
EOF
{ echo "$TITLE"; cat "$BODY_FILE"; } | $SKILL_DIR/scripts/check-no-ai-trace.py --stdin
```

**Demande confirmation** (« Je pousse et j'ouvre la PR ? »), puis :
```bash
git push
gh pr create --base main --title "$TITLE" --body-file "$BODY_FILE" --assignee @me
# travail encore en cours ? ajoute --draft
```

Donne l'URL de la PR à l'utilisateur.

## 5. CI et relecture

**Suivre la CI** :
```bash
gh pr checks <N> --watch        # bloquant : lance-le en arrière-plan si c'est long
```

**Si la CI échoue** :
```bash
gh run list --branch <branche> --limit 3
gh run view <run-id> --log-failed
```
Corrige en local, fais un commit (`fix: …`, `test: …`, `style: …` selon la cause), puis `git push`. La CI se relance toute seule.

**Si le titre de PR est refusé** : `gh pr edit <N> --title "feat(scope): …"`. Le check se relance tout seul quand le titre change. L'ancien ✗ reste visible dans la liste des checks, mais seul le dernier résultat compte pour la fusion.

**Relecture** :
- En solo : relis le diff complet (`gh pr diff <N>`) et résume-le à l'utilisateur pour qu'il valide. C'est son filet de sécurité.
- En équipe : demande une relecture avec `gh pr edit <N> --add-reviewer <pseudo>`. Le reste est dans `team.md`.

## 6. Fusionner et nettoyer

Demande confirmation, puis :

```bash
gh pr merge <N> --squash --delete-branch
```

Si GitHub refuse la fusion alors que tout est vert (« base branch policy prohibits the merge »), voir `troubleshooting.md` § « PR bloquée alors que tout est vert ».

Si les checks tournent encore, `gh pr merge <N> --squash --auto --delete-branch` fusionnera automatiquement quand ils seront verts.

GitHub crée alors **un seul commit** sur `main`, avec le titre de la PR suivi de ` (#N)`, signé par GitHub. L'issue liée se ferme, et la branche distante est supprimée.

**Nettoyage local** :
```bash
git switch main
git pull
gh pr view <N> --json state --jq .state          # doit afficher MERGED
git branch -D <branche> 2>/dev/null || true      # -D est nécessaire, voir ci-dessous
gh issue view <N-issue> --json state --jq .state # CLOSED
```

Pourquoi `-D` et pas `-d` : après un squash, le commit dans `main` est **nouveau**. Git ne reconnaît pas les commits de la branche comme fusionnés, et `-d` refuse de la supprimer. C'est normal. On vérifie d'abord que la PR est bien `MERGED`, puis on force la suppression.

**Récap** : PR fusionnée (lien), issue fermée, retour sur `main` à jour, prochaine tâche possible. Si les releases automatiques sont actives et que la PR était un `feat` ou un `fix`, signale que release-please va ouvrir ou mettre à jour sa PR de release.
