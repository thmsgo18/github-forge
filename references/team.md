# Travail en équipe

`SKILL_DIR=~/.claude/skills/github-forge`.

## Passer un dépôt en mode équipe

1. **Inviter les coéquipiers** : chacun reçoit un e-mail d'invitation. Demande confirmation, car c'est une action visible.
   ```bash
   gh api -X PUT repos/OWNER/REPO/collaborators/<pseudo> -f permission=push
   gh api repos/OWNER/REPO/invitations --jq '.[] | .invitee.login'   # invitations en attente
   ```
   `push` permet de créer des branches et des PR. Seul le propriétaire est `admin` et peut changer les réglages.
2. **CODEOWNERS** : ajoute les pseudos dans `.github/CODEOWNERS` (par une PR). GitHub demandera automatiquement leur relecture.
   ```
   * @<pseudo> @alice @bob
   ```
3. **Protection en mode équipe** :
   ```bash
   $SKILL_DIR/scripts/protect-main.sh OWNER/REPO team "CI" "PR title"
   ```
   Elle ajoute 1 approbation obligatoire, l'annulation de l'approbation si un nouveau commit arrive, une branche à jour avec `main` et l'obligation de résoudre les discussions avant la fusion. Les commits signés ne sont pas exigés en équipe, sauf avec `--signatures` si chaque coéquipier a configuré la signature : un seul commit non signé bloquerait sa PR.
4. **CONTRIBUTING.md** : vérifie que la section équipe est présente (relecture obligatoire, comment installer les hooks).

## Se coordonner

- **Une issue par personne et par tâche**, assignée. Personne ne commence une tâche qui n'est pas à son nom. C'est ce qui évite que deux personnes modifient le même fichier en parallèle.
- Des **petites PR fusionnées vite** : moins elles restent ouvertes, moins il y a de conflits.
- Après chaque fusion d'un coéquipier, mets ta branche à jour (`git fetch origin && git merge origin/main`).

## Relire la PR d'un coéquipier

La relecture est publiée sous le nom de l'utilisateur. Elle est dans la langue du dépôt, sans aucune mention d'IA, précise et bienveillante. Rédige-la, montre-la à l'utilisateur, et ne la publie qu'avec son accord.

```bash
gh pr list --search "review-requested:@me"
gh pr view <N>                 # description, issue liée
gh pr diff <N>                 # le diff complet
gh pr checkout <N>             # pour tester en local
<commande de test du projet>
git switch main                # revenir après le test
```

Ce qu'il faut regarder, dans cet ordre :
1. **Correction** : le code fait-il ce que dit l'issue ? Les cas limites sont-ils gérés ?
2. **Tests** : les nouveaux comportements sont-ils testés ?
3. **Lisibilité** : noms, découpage, duplication.
4. **Convention** : titre de la PR, `Closes #N`.

Pour publier :
```bash
gh pr review <N> --approve -b "Looks good — clear and well tested. Thanks!"
gh pr review <N> --request-changes -b "$(cat <<'EOF'
Thanks for this! Two things before merging:

1. `cart.js:42` — quantities can still go negative when decrementing from 1.
2. Could you add a test for the empty-cart checkout?
EOF
)"
gh pr review <N> --comment -b "Non-blocking: consider extracting the price formatting into a helper."
```

Un commentaire bloquant explique **le problème et pourquoi**, et propose une piste. Un commentaire non bloquant commence par « Non-blocking: » ou « Nit: ».

## Recevoir une relecture sur sa PR

```bash
gh pr view <N> --comments
```

Corrige avec de nouveaux commits sur la même branche, puis `git push`. Réponds à chaque commentaire : « Done in abc1234 », ou explique pourquoi tu gardes ta version. Quand tout est traité, redemande une relecture :
```bash
gh pr edit <N> --add-reviewer <pseudo>
```

Rappel : GitHub ne permet pas d'approuver sa propre PR. En équipe, quelqu'un d'autre doit toujours approuver.

## Sans protection GitHub

Sur un dépôt privé d'une organisation gratuite (ou d'un compte sans Pro), GitHub refuse les rulesets : `protect-main.sh` s'arrête avec une erreur 403 et dit quelle offre manque. Si l'équipe ne veut ni payer ni rendre le dépôt public, la règle « jamais de commit direct sur `main` » passe par des hooks Git locaux, versionnés avec le projet :

- **husky** : copie `assets/hooks/guard-main-pre-commit` dans `.husky/pre-commit` (à la suite des lignes existantes, comme `npx lint-staged`) et `assets/hooks/guard-main-pre-push` dans `.husky/pre-push`. Projet dans un sous-dossier : dans `app/.husky/`.
- **pre-commit** : décommente le hook `no-commit-to-branch` dans `.pre-commit-config.yaml`.
- `{{MAIN_RULE}}` de `CONTRIBUTING.md` prend la version « hooks locaux » (`repo-setup.md` § 4).

Teste les deux refus avant de committer : sur `main`, `git commit --allow-empty -m "chore: test"` doit échouer, et `git push --dry-run origin HEAD:main` aussi, depuis une branche qui a un commit d'avance (sans commit à pousser, le hook ne reçoit rien).

Ce n'est qu'une garde : `--no-verify` la contourne, et un clone où `npm ci` n'a pas été lancé n'a pas les hooks. L'audit la compte comme un avertissement, pas comme une protection.

## Relire sans protection : cliquer sur « Approve »

Sans ruleset, GitHub laisse fusionner une PR qui n'a aucune approbation. Rappelle au relecteur de cliquer sur **Approve** avant de fusionner : c'est ce qui laisse une trace de la relecture dans la PR.

## Relectures automatiques de Copilot

Si Copilot est réglé pour relire chaque PR, il laisse sur chacune un commentaire. « Copilot was unable to review this pull request… insufficient remaining quota » n'est pas une relecture : il n'y a rien à corriger. Pour ne plus le recevoir, l'utilisateur désactive la relecture automatique dans ses réglages Copilot sur GitHub (réglage de son compte : ne le change pas pour lui).

## PR qui dépendent les unes des autres

Avec le squash merge, évite d'empiler une branche sur une autre : après la fusion de la première, la seconde porte encore ses anciens commits. Préfère des branches qui partent toutes de `main` et touchent des fichiers différents, et indique l'ordre de fusion dans la description (« À fusionner après #13 et #14 : le README pointe vers `Idea.md` »). Deux PR qui modifient les mêmes lignes (fin du README, `package.json`) entrent en conflit : regroupe ces modifications dans une seule PR.
