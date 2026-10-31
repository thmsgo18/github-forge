# Contributing to github-forge

Thanks for taking the time to contribute. Bug reports, fixes and new ideas are all welcome.

## Reporting a bug

Open an [issue](https://github.com/thmsgo18/github-forge/issues) with:

- what you asked Claude, or the exact script command you ran,
- what you expected and what happened instead (full output),
- your environment: OS, `git --version`, `gh --version`, `python3 --version`.

For a security issue, do not open a public issue: see [SECURITY.md](SECURITY.md).

## Suggesting a feature

Open an issue describing the situation the skill handles badly before writing anything, so we can agree on the approach. Real cases from real repositories are the most useful.

## Development setup

Clone the repository anywhere and link it as a personal skill, so your edits apply immediately:

```bash
git clone https://github.com/thmsgo18/github-forge.git
ln -s "$PWD/github-forge" ~/.claude/skills/github-forge
cd github-forge
pre-commit install
```

## Running the checks

These are the commands CI runs on every pull request:

```bash
python3 -m py_compile scripts/*.py
for f in scripts/*.sh; do bash -n "$f"; done
python3 scripts/check-no-ai-trace.py --head
```

Test a script change on a real repository too: `doctor.sh` from any folder, `audit-repo.py` from inside a repository you own.

## Project conventions

- `SKILL.md` and `references/` are written in French, like the conversations the skill has. Scripts keep English code comments and French output.
- `SKILL.md` stays short: it routes to one guide per situation. Detailed procedures go in `references/`.
- Scripts only use `git`, `gh` and `python3`, never write to GitHub without being asked, and print a clear next step when something fails.
- Commits and pull request titles follow [Conventional Commits](https://www.conventionalcommits.org/). The title becomes the commit on `main` (squash merge).

## Submitting a pull request

1. Fork the repository and create a branch from `main`.
2. Make your change, and check it on a real repository when it touches a script.
3. Run the checks above.
4. Open a pull request that explains what changed and why.
