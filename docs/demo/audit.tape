# Hero GIF: auditing a public repository against the github-forge standards.
# Regenerate from the repository root: vhs docs/demo/audit.tape (needs gh logged in)
Output docs/assets/demo-audit.gif

Require gh
Require git

Set FontSize 14
Set Width 1000
Set Height 660
Set Padding 18
Set Theme "Catppuccin Mocha"
Set TypingSpeed 45ms

# Throwaway clone so the recording shows no personal path.
Hide
Type `rm -rf /tmp/demo && mkdir -p /tmp/demo && cd /tmp/demo && git clone -q https://github.com/thmsgo18/github-forge-sandbox.git && cd github-forge-sandbox`
Enter
Type `export PATH="$HOME/.claude/skills/github-forge/scripts:$PATH" && clear`
Enter
Sleep 4s
Show

Type "audit-repo.py"
Sleep 500ms
Enter
Sleep 12s
