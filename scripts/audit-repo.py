#!/usr/bin/env python3
"""Read-only audit of a repository against github-forge standards.

Usage: audit-repo.py [OWNER/REPO]
Run it from inside the repository. OWNER/REPO defaults to the origin remote.
Prints a Markdown checklist (✓ ok, ✗ to fix, ⚠ warning) and a score.
"""
import json
import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

FILES = [
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    ".gitignore",
    ".editorconfig",
    ".gitattributes",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/CODEOWNERS",
    ".github/dependabot.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/pr-title.yml",
]
SENSITIVE = re.compile(r"(^|/)(\.env(\.local)?|\.DS_Store|CLAUDE(\.local)?\.md|id_rsa|.*\.pem)$|(^|/)\.claude/")


def run(*cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip()


def gh_json(path):
    code, out = run("gh", "api", path)
    if code != 0 or not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


class Report:
    def __init__(self):
        self.ok_count = self.ko_count = self.warn_count = 0

    def section(self, title):
        print(f"\n## {title}\n")

    def ok(self, msg):
        self.ok_count += 1
        print(f"- ✓ {msg}")

    def ko(self, msg):
        self.ko_count += 1
        print(f"- ✗ {msg}")

    def warn(self, msg):
        self.warn_count += 1
        print(f"- ⚠ {msg}")

    def info(self, msg):
        print(f"- · {msg}")

    def check(self, condition, ok_msg, ko_msg, soft=False):
        if condition:
            self.ok(ok_msg)
        elif soft:
            self.warn(ko_msg)
        else:
            self.ko(ko_msg)


def tracked(path):
    return run("git", "ls-files", "--error-unmatch", path)[0] == 0


def tracked_matching(pattern):
    """Tracked paths matching a regex, anywhere in the tree (hooks may live in app/.husky/)."""
    regex = re.compile(pattern)
    return [f for f in run("git", "ls-files")[1].splitlines() if regex.search(f)]


def main_guard_hooks():
    """Tracked pre-commit / pre-push hooks that refuse work on main (local guard, see team.md)."""
    found = []
    for path in tracked_matching(r"(^|/)(\.husky|\.githooks)/(pre-commit|pre-push)$"):
        try:
            with open(path, encoding="utf-8") as fh:
                if re.search(r"\bmain\b", fh.read()):
                    found.append(path)
        except OSError:
            pass
    return found


def workflow_job_names():
    names = set()
    wf_dir = ".github/workflows"
    if os.path.isdir(wf_dir):
        for name in os.listdir(wf_dir):
            if name.endswith((".yml", ".yaml")):
                with open(os.path.join(wf_dir, name), encoding="utf-8") as fh:
                    for match in re.finditer(r"^\s{4}name:\s*['\"]?([^'\"\n#]+?)['\"]?\s*(#.*)?$", fh.read(), re.M):
                        names.add(match.group(1).strip())
    return names


def audit_files(rep):
    rep.section("Fichiers du projet")
    for path in FILES:
        if tracked(path):
            rep.ok(path)
        elif os.path.exists(path):
            rep.warn(f"{path} présent mais pas commité")
        else:
            rep.ko(f"{path} manquant")
    if os.path.exists("release-please-config.json"):
        rep.check(os.path.exists(".github/workflows/release.yml"),
                  "releases automatiques (release-please)",
                  "release-please-config.json sans workflow .github/workflows/release.yml")
    else:
        rep.info("releases automatiques non configurées (optionnel)")
    husky = tracked_matching(r"(^|/)\.husky/commit-msg$")
    precommit = tracked_matching(r"(^|/)\.pre-commit-config\.yaml$")
    if husky or precommit:
        rep.ok("hooks de commit configurés (" + (f"husky, {husky[0]}" if husky else f"pre-commit, {precommit[0]}") + ")")
        _, hooks_path = run("git", "config", "core.hooksPath")
        hooks_path = hooks_path or run("git", "rev-parse", "--git-path", "hooks")[1]
        installed = os.path.exists(os.path.join(hooks_path, "commit-msg"))
        rep.check(installed, "hook commit-msg installé sur cette machine",
                  "hooks pas installés ici : lancer « npm install » (husky) ou « pre-commit install »", soft=True)
    else:
        rep.ko("aucun hook de commit (husky ou pre-commit)")


def audit_local(rep):
    rep.section("Hygiène locale")
    _, head = run("git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    default = head.replace("origin/", "") if head else run("git", "branch", "--show-current")[1]
    rep.check(default == "main", "branche par défaut : main", f"branche par défaut : {default} (renommer en main)")
    _, files = run("git", "ls-files")
    bad = [f for f in files.splitlines() if SENSITIVE.search(f)]
    rep.check(not bad, "aucun fichier sensible ou local versionné", "fichiers à retirer du dépôt : " + ", ".join(bad[:10]))
    code, out = run(sys.executable, os.path.join(SCRIPT_DIR, "check-no-ai-trace.py"), "--head")
    if code == 0:
        rep.ok("aucune trace d'IA dans l'historique")
    elif code == 1:
        n = sum(1 for line in out.splitlines() if line.startswith("✗"))
        rep.ko(f"{n} trace(s) d'IA dans l'historique (voir audit.md § 4)")
    else:
        rep.warn("vérification des traces d'IA impossible")


def audit_remote(rep, repo):
    data = gh_json(f"repos/{repo}")
    if data is None:
        rep.section("GitHub")
        rep.warn(f"dépôt {repo} introuvable ou gh non connecté : partie distante ignorée")
        return
    public = data.get("visibility") == "public"

    rep.section("Réglages GitHub")
    rep.check(bool(data.get("description")), "description renseignée", "pas de description", soft=True)
    rep.check(bool(data.get("topics")), "topics : " + ", ".join(data.get("topics") or []), "pas de topics", soft=True)
    rep.check(bool(data.get("license")), f"licence détectée par GitHub : {(data.get('license') or {}).get('spdx_id')}",
              "aucune licence détectée par GitHub", soft=not public)
    rep.check(data.get("default_branch") == "main", "branche par défaut GitHub : main",
              f"branche par défaut GitHub : {data.get('default_branch')}")
    squash_only = data.get("allow_squash_merge") and not data.get("allow_merge_commit") and not data.get("allow_rebase_merge")
    rep.check(squash_only, "fusion : squash uniquement", "d'autres méthodes de fusion que le squash sont autorisées")
    rep.check(data.get("squash_merge_commit_title") == "PR_TITLE", "commit de squash = titre de la PR",
              f"titre du commit de squash : {data.get('squash_merge_commit_title')} (attendu PR_TITLE)")
    rep.check(data.get("delete_branch_on_merge"), "branches supprimées après fusion", "branches pas supprimées après fusion")
    rep.check(data.get("allow_auto_merge"), "auto-merge disponible", "auto-merge désactivé", soft=True)

    rep.section("Protection et sécurité")
    code, out = run("gh", "api", f"repos/{repo}/rulesets")
    plan_blocks = code != 0 and re.search(r"upgrade|403", out, re.I) is not None
    try:
        rulesets = json.loads(out) if code == 0 else []
    except json.JSONDecodeError:
        rulesets = []
    rs_id = next((r["id"] for r in rulesets if r.get("name") == "Protect main"), None)
    if rs_id:
        rs = gh_json(f"repos/{repo}/rulesets/{rs_id}") or {}
        rules = {r["type"]: r.get("parameters", {}) for r in rs.get("rules", [])}
        rep.check(rs.get("enforcement") == "active", "ruleset « Protect main » actif",
                  f"ruleset « Protect main » en mode {rs.get('enforcement')}")
        pr = rules.get("pull_request")
        if pr is not None:
            approvals = pr.get("required_approving_review_count", 0)
            rep.ok(f"PR obligatoire — mode {'équipe' if approvals else 'solo'} ({approvals} approbation(s))")
        else:
            rep.ko("le ruleset n'exige pas de PR")
        for rule, label in (("non_fast_forward", "force-push interdit"), ("deletion", "suppression de main interdite"),
                            ("required_linear_history", "historique linéaire"), ("required_signatures", "commits signés exigés")):
            rep.check(rule in rules, label, f"règle manquante : {label}")
        checks = [c["context"] for c in rules.get("required_status_checks", {}).get("required_status_checks", [])]
        if checks:
            rep.ok("checks obligatoires : " + ", ".join(checks))
            missing = [c for c in checks if c not in workflow_job_names()]
            if missing:
                rep.warn("checks exigés sans job correspondant dans les workflows : " + ", ".join(missing))
        else:
            rep.ko("aucun check obligatoire (la CI ne bloque pas la fusion)")
    elif gh_json(f"repos/{repo}/branches/main/protection"):
        rep.warn("main protégée par l'ancienne méthode (branch protection) : migrer vers le ruleset avec protect-main.sh")
    elif plan_blocks:
        org = (data.get("owner") or {}).get("type") == "Organization"
        offer = "GitHub Team ou dépôt public" if org else "GitHub Pro (Student Pack) ou dépôt public"
        guards = main_guard_hooks()
        if guards:
            rep.warn(f"protection GitHub indisponible ({offer}) : main gardée localement par " + ", ".join(guards))
        else:
            rep.ko(f"protection GitHub indisponible ({offer}) et aucune garde locale de main (team.md § « Sans protection GitHub »)")
    else:
        rep.ko("main n'est pas protégée")

    if public:
        sa = data.get("security_and_analysis") or {}
        rep.check((sa.get("secret_scanning") or {}).get("status") == "enabled", "scan des secrets actif", "scan des secrets inactif")
        rep.check((sa.get("secret_scanning_push_protection") or {}).get("status") == "enabled",
                  "push bloqué s'il contient un secret", "blocage des push contenant un secret inactif")
    else:
        rep.info("dépôt privé : scan des secrets non disponible sans GitHub Secret Protection")
    rep.check(run("gh", "api", f"repos/{repo}/vulnerability-alerts")[0] == 0, "alertes Dependabot actives", "alertes Dependabot inactives")
    asf = gh_json(f"repos/{repo}/automated-security-fixes") or {}
    rep.check(asf.get("enabled"), "correctifs de sécurité automatiques actifs", "correctifs de sécurité automatiques inactifs")
    perms = gh_json(f"repos/{repo}/actions/permissions/workflow") or {}
    rep.check(perms.get("default_workflow_permissions") == "read", "workflows en lecture seule par défaut",
              "les workflows ont l'écriture par défaut (passer en read)", soft=True)

    if os.path.exists("release-please-config.json"):
        rep.section("Releases")
        rep.check(perms.get("can_approve_pull_request_reviews"), "les Actions peuvent créer la PR de release",
                  "les Actions ne peuvent pas créer de PR : configure-repo.sh --releases")
        secrets = gh_json(f"repos/{repo}/actions/secrets") or {}
        names = [s["name"] for s in secrets.get("secrets", [])]
        rep.check("RELEASE_PLEASE_TOKEN" in names, "token release-please présent",
                  "pas de RELEASE_PLEASE_TOKEN : la CI ne tournera pas sur la PR de release (voir releases.md)", soft=True)

    rep.section("Santé de la CI")
    code, out = run("gh", "run", "list", "-R", repo, "--branch", "main", "--workflow", "ci.yml", "--limit", "1",
                    "--json", "conclusion,status,url")
    runs = json.loads(out) if code == 0 and out else []
    if not runs:
        rep.info("aucune exécution de la CI sur main pour l'instant")
    else:
        last = runs[0]
        conclusion = last.get("conclusion") or last.get("status")
        rep.check(conclusion == "success", f"dernière CI sur main : succès", f"dernière CI sur main : {conclusion} — {last.get('url')}")


def main(argv):
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if run("git", "rev-parse", "--is-inside-work-tree")[0] != 0:
        print("Pas un dépôt Git : lance ce script depuis le dossier du projet.", file=sys.stderr)
        return 2
    os.chdir(run("git", "rev-parse", "--show-toplevel")[1])
    repo = argv[0] if argv else run("gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner")[1]

    print(f"# Audit github-forge — {repo or os.path.basename(os.getcwd())}")
    rep = Report()
    audit_files(rep)
    audit_local(rep)
    if repo:
        audit_remote(rep, repo)
    else:
        rep.section("GitHub")
        rep.info("pas de dépôt GitHub associé (remote origin absent)")

    total = rep.ok_count + rep.ko_count
    print(f"\n**Score : {rep.ok_count}/{total}** — {rep.ko_count} point(s) à corriger, {rep.warn_count} avertissement(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
