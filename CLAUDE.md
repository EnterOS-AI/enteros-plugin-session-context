# molecule-session-context — Session Start Context Loader

`molecule-session-context` is a **session-initialisation hook plugin** that
auto-loads recent cron-learnings and repo PR/issue counts at `SessionStart`.
Pairs with `molecule-cron-learnings`.

**Version:** 1.0.0
**Runtime:** `claude_code`

---

## Repository Layout

```
molecule-session-context/
├── plugin.yaml              — Plugin manifest
├── hooks/
│   └── session-start-context/
│       └── hook.json        — SessionStart hook definition
└── adapters/               — Harness adaptors
```

---

## What It Does

At the start of every session, this hook:
1. Reads the last N lines of `~/.claude/projects/<project>/cron-learnings.jsonl`
2. Loads current PR/issue counts for the workspace repo
3. Surfaces this context to the agent in the first response

This means the agent enters every session already knowing:
- What went wrong last time (from cron-learnings)
- How many open PRs and issues exist (context before acting)

---

## SessionStart Hook

The hook fires on every new session for a workspace. Configure how many
learnings to load via workspace settings:

```json
{
  "session_context": {
    "learnings_lines": 20,
    "include_pr_counts": true,
    "include_issue_counts": true
  }
}
```

---

## Development

### Prerequisites

- Python 3.11+
- `gh` CLI authenticated
- Write access to `Molecule-AI/molecule-ai-plugin-molecule-session-context`

### Setup

```bash
git clone https://github.com/Molecule-AI/molecule-ai-plugin-molecule-session-context.git
cd molecule-ai-plugin-molecule-session-context

# YAML validation
python3 -c "import yaml; yaml.safe_load(open('plugin.yaml'))"
```

### Pre-Commit Checklist

```bash
# YAML structure
python3 -c "import yaml; yaml.safe_load(open('plugin.yaml'))"

# Credential scan
python3 -c "
import re, sys
with open('plugin.yaml') as f:
    content = f.read()
patterns = [r'sk.ant', r'ghp.', r'AKIA[A-Z0-9]']
if any(re.search(p, content) for p in patterns):
    print('FAIL: possible credentials found')
    sys.exit(1)
print('No credentials: OK')
"
```

---

## Release Process

1. Review changes: `git log origin/main..HEAD --oneline`
2. Bump `version` in `plugin.yaml` (semver)
3. Commit: `chore: bump version to X.Y.Z`
4. Tag and push: `git tag vX.Y.Z && git push origin main --tags`
5. Create GitHub Release with changelog

---

## Known Issues

See `known-issues.md` at the repo root.
