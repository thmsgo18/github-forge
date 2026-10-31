# Contribuer à {{PROJECT_NAME}}

Une règle guide tout le reste : **`main` fonctionne toujours**. Tout changement passe par une branche courte et une pull request.

## Le cycle d'une tâche

1. **Partir d'une issue.** Chaque fonctionnalité ou bug a son issue, assignée à une seule personne. La maintenance (`chore`, `docs`, `ci`, `build`) peut s'en passer.
2. **Créer une branche** depuis un `main` à jour :
   ```bash
   git switch main && git pull
   git switch -c feat/12-description-courte
   ```
3. **Committer** par petites étapes cohérentes qui fonctionnent, au format [Conventional Commits](#messages-de-commit).
4. **Ouvrir une pull request** vers `main` :
   - le **titre** suit Conventional Commits : c'est lui qui devient le commit dans `main` ;
   - la **description** suit le modèle et contient `Closes #12`.
5. **Les vérifications doivent passer** (CI et titre de la PR).{{TEAM_RULE}}
6. La PR est fusionnée en **Squash and merge**. La branche est supprimée automatiquement.

{{MAIN_RULE}}

## Noms de branches

`<type>/<numéro-issue>-<description-courte>`, en minuscules, sans accents, mots séparés par des tirets. Sans issue : `<type>/<description-courte>`.

```
feat/12-connexion-google
fix/27-quantite-negative
chore/mise-a-jour-ci
```

## Messages de commit

Format : `<type>(<scope facultatif>): <description>`, en français, à l'infinitif, sans point final, 72 caractères maximum.

```
feat(auth): ajouter la connexion Google
fix(panier): empêcher les quantités négatives
docs(readme): décrire l'installation
```

| Type | Pour |
|---|---|
| `feat` | Une nouvelle fonctionnalité |
| `fix` | La correction d'un bug |
| `docs` | La documentation seule |
| `refactor` | Une restructuration sans changement de comportement |
| `perf` | Une amélioration de performance |
| `test` | L'ajout ou la correction de tests |
| `build` | Le build ou les dépendances |
| `ci` | La configuration de la CI |
| `chore` | La maintenance et l'outillage |
| `style` | Le formatage seul |
| `revert` | L'annulation d'un commit |

Un changement cassant ajoute `!` après le type et un pied de message `BREAKING CHANGE:` qui explique la migration.

## Installation

```bash
git clone https://github.com/{{OWNER}}/{{REPO}}.git
cd {{REPO}}
{{INSTALL_COMMAND}}
{{HOOKS_INSTALL_LINE}}
```

Les hooks Git vérifient le format et les messages avant chaque commit. Un hook qui refuse signale un vrai problème : on corrige la cause plutôt que de le contourner avec `--no-verify`.

Avant d'ouvrir une pull request, lancer les tests :

```bash
{{TEST_COMMAND}}
```

## Garder sa branche à jour

```bash
git fetch origin
git merge origin/main
```

## Signaler un bug ou proposer une idée

Utiliser les [modèles d'issue](../../issues/new/choose). Pour un problème de sécurité, ne pas ouvrir d'issue publique : contacter directement le mainteneur.
