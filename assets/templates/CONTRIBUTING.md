# Contributing to {{PROJECT_NAME}}

Thanks for taking the time to contribute! This project follows a simple, strict workflow so that `main` always works.

## Workflow

We use [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow):

1. **Start from an issue.** Every change is tracked by an issue. Pick an open one (and assign yourself) or open a new one using the templates.
2. **Create a branch** from an up-to-date `main`:
   ```bash
   git switch main && git pull
   git switch -c feat/12-short-description
   ```
3. **Commit** small, coherent steps using [Conventional Commits](#commit-messages).
4. **Open a pull request** against `main`:
   - the **title** follows Conventional Commits (it becomes the commit message on `main`);
   - the **description** follows the template and contains `Closes #12`.
5. **Checks must pass** (CI and PR title).{{TEAM_RULE}}
6. The PR is merged with **Squash and merge** and the branch is deleted automatically.

{{MAIN_RULE}}

## Branch names

`<type>/<issue-number>-<short-description>` — lowercase, words separated by hyphens.

```
feat/12-google-sign-in
fix/27-negative-cart-quantity
docs/31-install-instructions
```

## Commit messages

Format: `<type>(<optional scope>): <description>` — imperative mood, lowercase, no trailing period, 72 characters max.

| Type | Use it for |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |
| `test` | Adding or fixing tests |
| `build` | Build system or dependencies |
| `ci` | CI configuration |
| `chore` | Maintenance and tooling |
| `style` | Formatting only |
| `revert` | Reverting a previous commit |

Breaking changes add `!` after the type and a `BREAKING CHANGE:` footer:

```
feat(api)!: remove v1 endpoints

BREAKING CHANGE: /v1/* routes are gone. Use /v2/* instead.
```

## Local setup

```bash
git clone https://github.com/{{OWNER}}/{{REPO}}.git
cd {{REPO}}
{{INSTALL_COMMAND}}
{{HOOKS_INSTALL_LINE}}
```

Git hooks check formatting and commit messages before each commit. Please don't bypass them.

Run the tests before opening a pull request:

```bash
{{TEST_COMMAND}}
```

## Keeping your branch up to date

```bash
git fetch origin
git merge origin/main
```

## Reporting bugs and requesting features

Use the [issue templates](../../issues/new/choose). For security issues, please do not open a public issue — contact the maintainer directly.
