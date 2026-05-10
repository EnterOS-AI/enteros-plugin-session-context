# molecule-session-context

Auto-loads recent learnings and workspace activity at session start. Pairs with `molecule-skill-cron-learnings` — together they give the agent a running summary of past decisions and current state before beginning work.

## What it loads

1. **Recent learnings** — reads the last 10 entries from `~/.molecule/cron-learnings.jsonl` (written by `molecule-skill-cron-learnings`)
2. **Repo activity** — runs `git log --oneline -10` to surface recent commits
3. **Issue counts** — runs `gh issue list --state open` to show open items

All output is emitted as `additionalContext` on `SessionStart`.

## Install

### In org template (org.yaml)

```yaml
plugins:
  - molecule-session-context
```

**Recommended:** Also install `molecule-skill-cron-learnings` to populate the learnings file.

### From URL (community install)

```
github://Molecule-AI/molecule-ai-plugin-molecule-session-context
```

## Usage

No configuration needed. Install to activate — the hook fires on every session start.

## Hooks

- **SessionStart** — reads learnings + git log + issue counts, emits as context

## Architecture

```
hooks/
  session-start-context.py   # Reads learnings, git, gh; emits additionalContext
  session-start-context.sh   # Shell wrapper
  _lib.py                     # Shared helpers
adapters/
  claude_code.py              # Registers hook
settings-fragment.json        # Declares SessionStart hook binding
```

## Runtime

- `claude_code` — primary

## Known issues

See [known-issues.md](known-issues.md).

## License

Business Source License 1.1 — © Molecule AI.
