# Security Policy

## Supported versions

Only the latest release is supported with security fixes. Please upgrade before reporting an issue.

## Reporting a vulnerability

Please do not open a public issue for security problems.

Report it privately through [GitHub's private vulnerability reporting](https://github.com/thmsgo18/github-forge/security/advisories/new).

Include the affected version or commit, the steps to reproduce, and the impact you see. You can expect a first answer within a few days. Confirmed issues are fixed as fast as possible and credited in the release notes, unless you prefer to stay anonymous.

## Scope

- The scripts run locally with your own `git` and `gh` login. They read repository state and the GitHub API; only `configure-repo.sh` and `protect-main.sh` change settings, and only when you run them.
- The skill never reads, prints or stores a token. When a secret is needed (for release-please), you create it and run `gh secret set` yourself.
- `check-no-ai-trace.py` reads commit messages and file names only, never file contents.
- Nothing is sent anywhere other than GitHub.
