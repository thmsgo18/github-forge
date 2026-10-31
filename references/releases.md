# Versions et releases

`SKILL_DIR=~/.claude/skills/github-forge`.

## Semantic Versioning

Le format est `MAJEUR.MINEUR.CORRECTIF`, par exemple `1.4.2`.

| Commit fusionné | Nouvelle version | Signification pour l'utilisateur du projet |
|---|---|---|
| `fix:` / `perf:` | 1.4.2 → 1.4.**3** | « Rien ne change, ça marche mieux » |
| `feat:` | 1.4.2 → 1.**5**.0 | « Il y a du nouveau, rien ne casse » |
| `feat!:` / `BREAKING CHANGE:` | 1.4.2 → **2**.0.0 | « Attention, tu dois adapter ton code » |
| `docs`, `test`, `ci`, `chore`, `refactor`, `style`, `build` | pas de release | invisible pour l'utilisateur |

Tant que la version est en **0.x**, le projet est jeune et instable : un changement cassant fait monter le minor (0.4 → 0.5). On passe en **1.0.0** quand l'API est stable et que d'autres peuvent compter dessus. C'est une décision de l'utilisateur : propose-la, n'impose rien.

## Option A : releases automatiques avec release-please

### Fonctionnement

1. On fusionne normalement des PR `feat` et `fix` dans `main`.
2. Le workflow `release.yml` ouvre ou met à jour une PR **« chore(main): release X.Y.Z »**. Elle contient le CHANGELOG généré et le nouveau numéro de version.
3. Quand on veut publier, on relit cette PR puis on la fusionne (squash).
4. release-please crée alors automatiquement le tag `vX.Y.Z` et la **GitHub Release** avec ses notes.

### Installer release-please

Copie les fichiers depuis `$SKILL_DIR/assets/release/`, par une PR si `main` est protégée :

| Fichier dans le projet | Source | À adapter |
|---|---|---|
| `release-please-config.json` | `assets/release/release-please-config.json` | `release-type` : `node`, `python`, `maven` ou `simple` (voir le tableau de `repo-setup.md` § 2). Déjà réglé : première version 0.1.0 (`initial-version`), tags `vX.Y.Z`, titre `chore: release X.Y.Z`, en-tête de PR neutre. Pour un projet déjà versionné, retire `initial-version` |
| `.release-please-manifest.json` | `assets/release/release-please-manifest.json` | `{".": "0.0.0"}`. Un projet déjà versionné met sa version actuelle et crée le tag correspondant (`git tag -a vX.Y.Z`) |
| `.github/workflows/release.yml` | `assets/workflows/release.yml` | — |

Pour le type `simple`, crée aussi un fichier `version.txt` contenant `0.0.0`. Si la CI vérifie le formatage (Prettier…), exclus `CHANGELOG.md`, qui est généré par release-please.

Le dépôt doit autoriser les Actions à créer des PR. `configure-repo.sh OWNER/REPO --releases` s'en charge.

### Le piège des checks sur la PR de release

Une PR créée par le jeton automatique des Actions (`GITHUB_TOKEN`) **ne déclenche pas les workflows**, par une règle de GitHub qui empêche les boucles infinies. La CI ne tourne donc pas sur la PR de release, et la protection de `main` bloque sa fusion. Il y a deux solutions.

**Solution recommandée : un token dédié.** L'utilisateur le crée lui-même. Ne manipule jamais sa valeur.
1. GitHub → Settings → Developer settings → Fine-grained tokens → Generate new token.
2. Nom `release-please-<repo>`, expiration à 1 an, *Repository access : Only select repositories* → ce dépôt.
3. Permissions : **Contents : Read and write**, **Pull requests : Read and write**.
4. Dans le dossier du projet, il lance `gh secret set RELEASE_PLEASE_TOKEN` et colle le token quand la commande le demande.

Le workflow l'utilise automatiquement s'il existe. Pense à lui rappeler la date d'expiration.

**Solution de secours sans token** : déclencher la CI sur la PR de release avec un commit vide poussé par l'utilisateur lui-même.
```bash
gh pr checkout <N-release>
git commit --allow-empty -m "ci: trigger checks"
git push
git switch main
```

release-please réécrira la branche à sa prochaine mise à jour. Il faudra recommencer si la PR change avant la fusion.

## Option B : release manuelle guidée

Quand l'utilisateur dit « fais une release » sur un dépôt sans release-please :

```bash
git switch main && git pull
LAST=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")
git log ${LAST:+$LAST..}HEAD --format='%s' --no-merges   # en "none", git log HEAD
```

1. Lis les commits depuis le dernier tag et calcule la version selon le tableau SemVer. Explique le calcul : « 2 feat et 1 fix depuis v0.3.1, donc v0.4.0 ».
2. Rédige les notes de version dans la langue du dépôt, classées par type (*Features*, *Bug Fixes*), sans mention d'IA. Montre-les à l'utilisateur.
3. Après confirmation :
   ```bash
   git tag -a v0.4.0 -m "v0.4.0"          # signé automatiquement (tag.gpgSign=true)
   git push origin v0.4.0
   gh release create v0.4.0 --verify-tag --title "v0.4.0" --notes-file <notes.md>
   ```
   Pour laisser GitHub générer les notes depuis les PR, utilise `--generate-notes` à la place de `--notes-file`.
4. Si le projet a un fichier de version (`package.json`…), mets-le à jour **avant** de taguer, par une PR `chore(release): 0.4.0`.

## Corriger une release ratée

- Tag mis sur le mauvais commit, pas encore utilisé par personne :
  ```bash
  gh release delete v0.4.0 --yes
  git push --delete origin v0.4.0
  git tag -d v0.4.0
  ```
  Puis recommence. Demande confirmation, car c'est une suppression.
- Release déjà utilisée par d'autres : ne la supprime pas. Publie une version corrective (`v0.4.1`).
