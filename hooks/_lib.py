"""Common helpers for Claude Code hooks. Imported by the .py hook scripts.

Hooks receive JSON on stdin per the Claude Code hook spec, and may emit
JSON on stdout or exit with code 2 to block. This module wraps both.
"""
import json
import os
import sys


def get_repo_root(hook_file: str) -> str:
    """Return the repo root given an absolute hook script path.

    When Claude Code invokes a hook via absolute path, __file__ resolves to
    e.g. /path/to/repo/hooks/session-start-context.py. Three dirname() calls
    from there land at the workspace parent (one level above the repo), not the
    repo root. We detect this overshoot by checking for the hooks/ marker.
    """
    abs_hook = os.path.abspath(hook_file)
    parent = os.path.dirname(abs_hook)          # hooks/
    repo = os.path.dirname(parent)              # repo/
    workspace = os.path.dirname(repo)           # workspace/ (parent of repo)
    # If parent still has hooks/ dir, we haven't overshot — return repo.
    # Otherwise the workspace level is the repo root.
    if os.path.isdir(os.path.join(repo, "hooks")):
        return repo
    return workspace


def read_input() -> dict:
    """Parse stdin JSON. Empty input → empty dict."""
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def emit(payload: dict) -> None:
    """Print JSON payload to stdout for the harness to interpret."""
    print(json.dumps(payload))


def deny_pretooluse(reason: str) -> None:
    """Emit a PreToolUse denial with reason and exit 0."""
    emit({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    })
    sys.exit(0)


def add_context(text: str) -> None:
    """Emit additionalContext for SessionStart / UserPromptSubmit hooks."""
    if text and text.strip():
        emit({"additionalContext": text})


def warn_to_stderr(msg: str) -> None:
    """Non-blocking warning visible to the next agent turn via stderr."""
    print(msg, file=sys.stderr)
