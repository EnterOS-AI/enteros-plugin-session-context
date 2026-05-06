# Local Development Setup

This runbook covers setting up a local development environment for
`molecule-session-context`.

---

## Prerequisites

- Python 3.11+
- `gh` CLI authenticated
- Write access to `Molecule-AI/molecule-ai-plugin-molecule-session-context`

---

## Clone & Bootstrap

```bash
git clone https://github.com/Molecule-AI/molecule-ai-plugin-molecule-session-context.git
cd molecule-ai-plugin-molecule-session-context
```

---

## Validating Plugin Structure

```bash
# YAML structure
python3 -c "import yaml; yaml.safe_load(open('plugin.yaml'))"
echo "plugin.yaml OK"

# Check all hook paths exist
python3 -c "
import yaml, os
with open('plugin.yaml') as f:
    data = yaml.safe_load(f)
for hook in data.get('hooks', []):
    path = f'hooks/{hook}/hook.json'
    exists = os.path.exists(path)
    print(f'[{\"OK\" if exists else \"MISSING\"}] {path}')
"
```

---

## Testing the SessionStart Hook

The harness wrapper is provided by the Molecule AI platform at runtime. To test:

1. Install the plugin in a test workspace
2. Start a new session
3. Verify the first agent response references recent learnings
4. Check the cron-learnings JSONL file has entries

---

## Simulating Session Context

To test without a live workspace:

```bash
# Create a mock learnings file
mkdir -p ~/.claude/projects/test-project
cat > ~/.claude/projects/test-project/cron-learnings.jsonl << 'EOF'
{"tick": "2026-04-21T00:00Z", "role": "test-lead", "learnings": ["GH_TOKEN expired — refresh needed", "PR template missing Testing section"]}
EOF

# Simulate session start (hook reads this file)
cat ~/.claude/projects/test-project/cron-learnings.jsonl
```

---

## Troubleshooting

### No context loaded at session start

- Verify `hooks/session-start-context/hook.json` is correctly named and placed
- Check the hook is registered in `plugin.yaml`
- Verify the workspace has read access to `~/.claude/projects/`

### Stale learnings

- The hook reads the JSONL file on every session start — check file permissions
- If learnings are not being appended, check `molecule-cron-learnings` is installed

---

## Related

- `molecule-cron-learnings` — appends learnings at end of each tick
- `molecule-workflow-retro` — generates weekly retrospectives from learnings
