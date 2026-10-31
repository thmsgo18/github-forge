#!/usr/bin/env python3
"""Detect AI attribution in commits, branch names, tracked files, or text.

Usage:
  check-no-ai-trace.py              commits of the current branch not yet on origin's default branch
                                    (whole history of HEAD when there is no remote)
  check-no-ai-trace.py <range>      a git revision range, e.g. origin/main..HEAD
  check-no-ai-trace.py --head       the whole history of HEAD only, plus tracked files
                                    (ignores other local branches, e.g. ones about to be dropped)
  check-no-ai-trace.py --all        every commit reachable from any ref, plus tracked files
  check-no-ai-trace.py --stdin      text read from standard input (PR or issue title and body)

Projects whose subject is Claude (a Claude Code skill, an app that drives Claude Code) can list
legitimate mentions in .github/ai-trace-allow: one regular expression per line, # for comments.
A line that matches one of them is not reported as a mention of Claude or Anthropic. Trailers,
the Anthropic noreply address and "generated with/by" are always reported.

Exit code: 0 = clean, 1 = trace found, 2 = usage or git error.
"""
import re
import subprocess
import sys

PATTERNS = [
    (r"co-authored-by:.*(claude|anthropic)", "trailer Co-Authored-By"),
    (r"noreply@anthropic\.com", "adresse noreply d'Anthropic"),
    (r"generated\s+(with|by)\s*\[?\s*(claude|chatgpt|copilot|gemini|an?\s+ai\b|ai\b|llm)", "mention « generated with/by »"),
    (r"claude\.(ai|com)", "lien vers Claude"),
    (r"\U0001F916", "emoji robot"),
    (r"\banthropic\b", "mention d'Anthropic"),
    (r"\bclaude\b", "mention de Claude"),
]
COMPILED = [(re.compile(p, re.IGNORECASE), label) for p, label in PATTERNS]
# Mentions that an allow list may excuse; attribution itself never is.
SOFT = {"mention de Claude", "mention d'Anthropic", "lien vers Claude"}
ALLOW_FILE = ".github/ai-trace-allow"
LOCAL_FILES = re.compile(r"(^|/)(CLAUDE(\.local)?\.md$|\.claude/)")


def git(*args):
    proc = subprocess.run(["git", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def load_allow():
    """Regular expressions from .github/ai-trace-allow at the repository root, if any."""
    try:
        root = git("rev-parse", "--show-toplevel").strip()
        with open(f"{root}/{ALLOW_FILE}", encoding="utf-8") as fh:
            lines = [l.strip() for l in fh]
    except (RuntimeError, OSError):
        return []
    return [re.compile(l, re.IGNORECASE) for l in lines if l and not l.startswith("#")]


ALLOW = []


def scan_text(text):
    """Return a list of (label, line) for every suspicious line."""
    hits = []
    for line in text.splitlines():
        for regex, label in COMPILED:
            if regex.search(line):
                if not (label in SOFT and any(a.search(line) for a in ALLOW)):
                    hits.append((label, line.strip()))
                break
    return hits


def default_base():
    try:
        ref = git("symbolic-ref", "--quiet", "refs/remotes/origin/HEAD").strip()
        return ref.replace("refs/remotes/", "")
    except RuntimeError:
        for candidate in ("origin/main", "origin/master"):
            try:
                git("rev-parse", "--verify", "--quiet", candidate)
                return candidate
            except RuntimeError:
                continue
    return None


def scan_commits(log_args):
    raw = git("log", "--format=%H%x00%s%x00%B%x1e", *log_args)
    findings, count = [], 0
    for record in raw.split("\x1e"):
        record = record.strip("\n")
        if not record:
            continue
        count += 1
        sha, subject, body = (record.split("\x00") + ["", ""])[:3]
        for label, line in scan_text(body):
            findings.append(f"✗ {sha[:8]} « {subject} » — {label} : {line}")
    return findings, count


def main(argv):
    findings = []
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    ALLOW.extend(load_allow())

    if argv and argv[0] == "--stdin":
        for label, line in scan_text(sys.stdin.read()):
            findings.append(f"✗ texte — {label} : {line}")
        scope = "texte vérifié"
    else:
        try:
            if argv and argv[0] == "--all":
                commit_findings, count = scan_commits(["--all"])
                files = git("ls-files").splitlines()
                scope = f"{count} commit(s) de tout l'historique"
            elif argv and argv[0] == "--head":
                commit_findings, count = scan_commits(["HEAD"])
                files = git("ls-files").splitlines()
                scope = f"{count} commit(s) de l'historique de HEAD"
            else:
                if argv:
                    rev_range = argv[0]
                else:
                    base = default_base()
                    rev_range = f"{base}..HEAD" if base else "HEAD"
                commit_findings, count = scan_commits([rev_range])
                base_ref = rev_range.split("..")[0] if ".." in rev_range else None
                files = git("diff", "--name-only", f"{base_ref}...HEAD").splitlines() if base_ref else git("ls-files").splitlines()
                scope = f"{count} commit(s) ({rev_range})"
                branch = git("branch", "--show-current").strip()
                for label, _ in scan_text(branch):
                    findings.append(f"✗ branche « {branch} » — {label}")
        except RuntimeError as err:
            print(f"Erreur git : {err}", file=sys.stderr)
            return 2
        findings.extend(commit_findings)
        for path in files:
            if LOCAL_FILES.search(path):
                findings.append(f"✗ fichier local versionné : {path}")

    if findings:
        print("\n".join(findings))
        print(f"\n{len(findings)} trace(s) d'IA trouvée(s) — {scope}. Corrige avant de publier.")
        return 1
    print(f"✓ Aucune trace d'IA — {scope}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
