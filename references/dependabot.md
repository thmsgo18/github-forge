# Trier les PR de Dependabot

Dependabot ouvre une PR par mise à jour (ou par groupe, selon `.github/dependabot.yml`). Le but : fusionner vite ce qui est sûr, vérifier ce qui peut casser, et ne jamais laisser `main` dans un état que la CI n'a pas validé.

`SKILL_DIR=~/.claude/skills/github-forge`.

## 1. Faire l'inventaire

```bash
gh pr list --author "app/dependabot" --json number,title,mergeable
for n in <numéros>; do gh pr checks $n; gh pr diff $n --name-only; done
```

Classe chaque PR :

| Cas | Exemple | Traitement |
|---|---|---|
| Correctif ou mineure, CI verte | `2.8.3 → 2.8.4` | Fusionner |
| Majeure, CI verte | `TypeScript 6 → 7` | Lire les notes de version (changements cassants) et chercher dans le code ce qui est retiré, puis fusionner |
| CI rouge à cause de la mise à jour | `zip 2 → 9` : `name()` renvoie un `Result` | Corriger le code sur la branche de la PR (§ 3) |
| CI rouge sans rapport avec la mise à jour | un test qui dépend du temps et qui échoue quand plusieurs CI tournent en même temps | Relancer le job (`gh run rerun <id> --failed`), puis corriger le test dans une PR à part |
| Paire front et back d'un même plugin | `@tauri-apps/plugin-dialog` (npm) et `tauri-plugin-dialog` (Cargo) | Fusionner les deux l'une après l'autre, pour garder les mêmes versions |

Lis le journal d'un échec avant de conclure : `gh run view <id> --log-failed`.

## 2. Fusionner dans le bon ordre

- Les PR qui touchent le même lockfile (`package-lock.json`, `Cargo.lock`) entrent souvent en conflit après la première fusion. Dependabot met alors les suivantes à jour sur `main` tout seul, en quelques minutes : attends que leur CI soit de nouveau verte.
- Commence par les GitHub Actions et les mineures, garde les majeures pour la fin, une par une.
- L'auteur de la PR étant Dependabot, l'utilisateur peut l'approuver lui-même. La relecture est publiée sous son nom, dans la langue du dépôt :

```bash
gh pr review <N> --approve -b "Mise à jour vérifiée : CI verte."
gh pr merge <N> --squash
```

Demande l'accord de l'utilisateur pour la série entière (« J'approuve et je fusionne les 7 PR dans cet ordre ? »), pas pour chacune.

## 3. Corriger une PR de Dependabot

```bash
gh pr checkout <N>
# corriger, lancer les tests et le lint en local
git commit -m "fix(<scope>): adapter <module> à <dépendance> <version>"
git push
```

Dès qu'un commit humain est ajouté, **Dependabot ne met plus cette PR à jour**. Fusionne-la donc avant les PR qui touchent le même lockfile, pour que ce soient elles qu'il mette à jour.

## 4. Vérifier `main` à la fin

Chaque PR n'a été testée que seule. Une fois tout fusionné, la CI de `main` valide la combinaison : attends son résultat, et lance aussi les tests en local sur `main` à jour. Si elle échoue, corrige par une nouvelle PR, sans revenir sur les fusions.
