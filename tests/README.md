# Test Rationale — molecule-session-context

## What this plugin does

`molecule-session-context` provides a SessionStart hook (`session-start-context.py`)
that injects operational context into Claude's context window at session start:
recent cron-learnings from JSONL, freeze-file status, and open PR/issue counts
from GitHub.

The hook reads `~/.claude/projects/.../memory/cron-learnings.jsonl` (written by
`molecule-cron-learnings`) and emits a JSON `additionalContext` payload to stdout.
It also queries `gh` for repo state and handles graceful degradation when
`gh` is unavailable or files are missing.

## What is tested

- `hooks/_lib.py` helpers: `read_input`, `emit`, `deny_pretooluse`, `add_context`,
  `warn_to_stderr`, `get_repo_root`
- `hooks/session-start-context.py` logic: `tail()` JSONL reader, `gh_count()`
  subprocess wrapper, full `main()` integration with mocked gh + tempfile learnings
- Hook error handling (exits 0 on exception, not crash)

## What is NOT unit-tested (and why)

- Real `gh` API calls — tested with `unittest.mock` subprocess interception
- Actual freeze-file reading — tested with mocked file I/O
- Integration with the workspace runtime's SessionStart hook harness —
  requires a real Claude Code session; covered by smoke + integration tests

## Running tests

```bash
python -m pytest tests/ -v
```
