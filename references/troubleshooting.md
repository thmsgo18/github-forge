# Dépannage

Pour chaque problème : le symptôme, la cause en une phrase pour l'utilisateur, puis les commandes. Avant toute opération qui modifie l'historique, fais une **copie de sauvegarde** : `git branch backup/<sujet>`. Elle ne coûte rien et permet de tout annuler.

## Sommaire
- Conflit de fusion
- PR bloquée alors que tout est vert
- Commits sur main par erreur
- Commits sur la mauvaise branche
- Annuler le dernier commit (pas encore poussé)
- Corriger le message du dernier commit
- Annuler des modifications locales
- Annuler une PR déjà fusionnée
- « Updates were rejected » au push
- `git pull` refuse : « Not possible to fast-forward »
- Un secret a été commité
- Un gros fichier a été commité
- Commit perdu, branche supprimée par erreur
- « detached HEAD »
- La signature échoue
- Le hook refuse le commit
- La CI échoue
- Des fichiers « 2 » apparaissent
- L'app en mode dev redémarre toute seule

---

## Conflit de fusion

**Symptôme** : `CONFLICT (content): Merge conflict in <fichier>` après `git merge origin/main`.
**Cause** : la même zone d'un fichier a été modifiée de deux façons différentes, et Git ne peut pas choisir à ta place.

```bash
git status                       # liste les fichiers « both modified »
```

Dans chaque fichier, Git a inséré des marqueurs (style zdiff3) :
```
<<<<<<< HEAD
ta version (ta branche)
||||||| a1b2c3d
la version d'origine (commit ancêtre commun), avant les deux modifications
=======
leur version (main)
>>>>>>> origin/main
```

Pour chaque bloc :
1. Lis les trois versions, et comprends ce que chaque côté voulait faire. Les deux intentions sont souvent à garder.
2. Écris la version finale, puis **supprime les lignes de marqueurs**.
3. Si l'intention n'est pas claire, demande à l'utilisateur (ou à l'auteur du code). Ne devine pas.

```bash
grep -nE '^(<<<<<<<|\|\|\|\|\|\|\||=======$|>>>>>>>)' <fichiers>   # doit ne rien afficher
<tests du projet>                                      # ça marche encore ?
git add <fichiers>
git commit -m "chore: merge main into <branche>"
```

Pour tout abandonner et revenir à l'état d'avant : `git merge --abort`.

## PR bloquée alors que tout est vert

**Symptôme** : les checks passent, mais `gh pr merge` répond « the base branch policy prohibits the merge », et la PR affiche *BLOCKED*.

```bash
gh pr view <N> --json mergeStateStatus,reviewDecision
gh api repos/OWNER/REPO/pulls/<N>/commits --jq '.[] | "\(.sha[0:7]) verified=\(.commit.verification.verified) \(.commit.verification.reason)"'
```

Les causes, dans l'ordre de probabilité :
1. **Un commit non vérifié** (`verified=false`), alors que le ruleset exige des signatures. GitHub vérifie chaque commit de la PR, même avec un squash. `unknown_key` veut dire que la clé de signature n'est pas déclarée sur le compte : voir `machine-setup.md` § 5. Si le commit vient d'un coéquipier qui ne signe pas, soit il configure la signature, soit on retire la règle avec `protect-main.sh OWNER/REPO team --no-signatures "CI" "PR title"`.
2. **Approbation manquante** (mode équipe) : `reviewDecision` vaut `REVIEW_REQUIRED`.
3. **Branche en retard sur main** (mode équipe, branche à jour exigée) : `git fetch origin && git merge origin/main && git push`.
4. **Discussion non résolue** (mode équipe) : réponds aux commentaires puis clique sur « Resolve conversation ».

## Commits sur main par erreur

**Symptôme** : des commits ont été faits sur `main` en local, ou `git pull` sur `main` dit « Not possible to fast-forward ».
**Cause** : on a oublié de créer une branche. Rien de grave tant que ce n'est pas poussé, et `main` est protégée de toute façon.

```bash
git switch main
git branch feat/<N>-<slug>          # 1. une branche garde tes commits
git fetch origin
git reset --hard origin/main        # 2. main revient à la version de GitHub
git switch feat/<N>-<slug>          # 3. on continue sur la branche
```

Le `reset --hard` jette les modifications qui ne sont pas encore commitées : vérifie d'abord avec `git status` que tout est commité ou sauvegardé.

## Commits sur la mauvaise branche

Les commits sont sur la branche A, mais auraient dû aller sur la branche B :
```bash
git log --oneline -5                 # repère les SHA à déplacer
git switch B
git cherry-pick <sha1> <sha2>        # copie les commits sur B
git switch A
git branch backup/A                  # sauvegarde
git reset --hard HEAD~2              # retire les 2 commits de A (seulement si A n'est pas poussée et partagée)
```

## Annuler le dernier commit (pas encore poussé)

```bash
git reset --soft HEAD~1    # annule le commit, garde les modifications dans l'index (prêtes à recommitter)
git reset HEAD~1           # annule le commit, garde les modifications dans les fichiers
```

Si le commit est déjà poussé sur sa propre branche, préfère `git revert` (voir plus bas), ou bien `reset` puis `git push --force-with-lease`, seulement si personne d'autre n'utilise la branche.

## Corriger le message du dernier commit

Pas encore poussé :
```bash
git commit --amend -m "fix(cart): prevent negative quantities"
```

Déjà poussé sur sa propre branche non partagée : même chose, puis `git push --force-with-lease`. Sur une branche en PR, c'est souvent inutile : seul le **titre de la PR** compte, puisque c'est lui qui devient le commit dans `main`.

## Annuler des modifications locales

```bash
git restore <fichier>              # revient à la dernière version commitée (perte définitive des changements)
git restore --staged <fichier>     # retire de l'index, garde les changements
git stash push -m "essai"          # met de côté (récupérable avec git stash pop)
git clean -nd                      # liste les fichiers non suivis qui seraient supprimés
git clean -fd                      # les supprime : demande confirmation
```

## Annuler une PR déjà fusionnée

Ne réécris jamais `main`. Crée un commit qui fait l'inverse, et fais-le passer par une PR.

```bash
git switch main && git pull
git switch -c revert/<N>-<slug>
git revert <sha-du-commit-squash>          # visible avec git log --oneline
git push
gh pr create --title 'revert: feat(auth): add Google sign-in' --body "Reverts #13 because <raison>."
```

Sur GitHub, le bouton **Revert** de la PR fusionnée fait la même chose.

## « Updates were rejected » au push

**Cause** : quelqu'un (ou toi depuis une autre machine) a poussé sur cette branche entre-temps.
```bash
git fetch origin
git merge origin/<branche>    # récupère son travail
git push
```

Ne force pas le push : tu écraserais son travail.

## `git pull` refuse : « Not possible to fast-forward »

Sur `main`, voir « Commits sur main par erreur ». Sur une branche de travail, voir « Updates were rejected ». Ce refus est voulu (`pull.ff=only`) : il évite de créer des commits de fusion sans s'en rendre compte.

## Un secret a été commité

**Révoque d'abord le secret** chez le fournisseur (nouvelle clé). C'est urgent si le dépôt est public, même si le commit n'est resté en ligne que quelques secondes.

- **Pas encore poussé** : retire le fichier de l'index, ajoute-le au `.gitignore`, puis `git commit --amend` (ou `reset` si c'est un commit plus ancien).
- **Push bloqué par GitHub** (push protection) : le blocage a fonctionné, rien n'est publié. Retire le secret des commits locaux (`git reset --soft origin/<branche>`, puis recommit sans le fichier) et pousse à nouveau.
- **Déjà publié** : une fois le secret révoqué, `git rm --cached`, `.gitignore`, puis un commit. Nettoyer l'historique est optionnel, la procédure est dans `audit.md` § 4.

## Un gros fichier a été commité

Au-delà de 100 Mo, GitHub refuse le push. Si ce n'est pas encore poussé :
```bash
git rm --cached <fichier> && echo "<fichier>" >> .gitignore
git commit --amend --no-edit      # si c'est dans le dernier commit
```

Si c'est dans un commit plus ancien de la branche, fais `git reset --soft origin/main`, retire le fichier, puis refais un commit propre. Pour des fichiers lourds qui doivent être versionnés (datasets, modèles), propose **Git LFS**.

## Commit perdu, branche supprimée par erreur

Git garde la trace de tout pendant au moins 30 jours :
```bash
git reflog                          # historique de toutes les positions de HEAD
git branch recovered <sha>          # recrée une branche sur le commit retrouvé
```

## « detached HEAD »

**Cause** : on a fait un checkout d'un commit ou d'un tag, pas d'une branche.
```bash
git switch -c <nouvelle-branche>    # pour garder ce qui a été fait ici
git switch main                     # ou simplement revenir
```

## La signature échoue

`error: Load key ... No such file` ou `error: gpg failed to sign the data` :
```bash
ls ~/.ssh/id_ed25519_signing*                  # la clé existe ?
git config --global user.signingKey            # pointe vers la clé privée ?
ssh-keygen -Y sign -n git -f ~/.ssh/id_ed25519_signing < /dev/null > /dev/null && echo OK
```

Voir `machine-setup.md` § 5. Le badge « Unverified » sur GitHub veut dire que la clé n'est pas déclarée sur le compte : `gh ssh-key list` doit lister une clé de type **signing**.

## Le hook refuse le commit

Le message explique la raison :
- **commitlint / conventional-pre-commit** : le message ne suit pas le format. Corrige-le, par exemple `feat(scope): description`, en minuscules et sans point final.
- **lint-staged / pre-commit** : le formateur a modifié des fichiers ou le linter a trouvé une erreur. Relance `git add` sur les fichiers modifiés et recommite, ou corrige l'erreur signalée.

N'utilise jamais `--no-verify` pour passer outre.

## La CI échoue

```bash
gh pr checks <N>
gh run view <run-id> --log-failed
```

Reproduis l'erreur en local avec la même commande que la CI, corrige, committe, puis pousse. Si l'échec vient de la CI elle-même (version d'outil, cache), corrige le workflow dans un commit `ci: …`.

## Des fichiers « 2 » apparaissent

**Symptôme** : `git status` montre des fichiers non suivis comme `SKILL 2.md` ou `LICENSE 2`. **Cause** : le dépôt est dans un dossier synchronisé par iCloud, qui crée une copie en conflit quand Git réécrit des fichiers. Compare chaque copie à l'original avant d'y toucher, puis mets à la corbeille celles qui sont identiques ou plus anciennes :

```bash
git ls-files --others --exclude-standard | grep ' 2'
cmp "fichier 2.md" "fichier.md" && echo identique
```

Solution durable : `machine-setup.md` § 8.

## L'app en mode dev redémarre toute seule

**Symptôme** : l'app lancée avec `tauri dev` (ou un autre serveur qui surveille les fichiers) se relance plusieurs fois sans qu'on y touche. **Cause** : des fichiers source ont changé sur le disque, souvent à cause d'un changement de branche, d'un rebase ou d'un outil qui régénère des fichiers (icônes, lockfile). Ce n'est pas le lanceur. Vérifie qu'une seule instance tourne (`ps -axo pid,lstart,command | grep "tauri dev"`), puis passe par un worktree pour les autres branches (`machine-setup.md` § 8).
