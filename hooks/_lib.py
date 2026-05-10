"""Common helpers for Claude Code hooks. Imported by the .py hook scripts.

Hooks receive JSON on stdin per the Claude Code hook spec, and may emit
JSON on stdout or exit with code 2 to block. This module wraps both.
"""
import json
import os
import sys


def get_repo_root(hook_file: str) -> str:
    """Return the repo root given a hook's __file__ path.

    The plugin is installed at <repo>/hooks/<hook>.py. We walk up three levels
    from __file__ to find the workspace root: hooks/ → repo/ → workspace/.
    When __file__ is absolute (Claude Code invokes hooks with absolute paths),
    the naive dirname chain overshoots by one level.

    Distinguishes the production layout (plugin installed as
    <workspace>/<plugin>/) from the dev layout (plugin IS the workspace)
    by checking whether the hook path places 'hooks/' as a direct
    subdirectory of the workspace. In dev layout, the hook is at
    <workspace>/hooks/<hook>.py so the relative path from workspace
    to hook starts with 'hooks/'. In production, the relative path
    starts with '<plugin>/hooks/' so does NOT start with 'hooks/'.

    - Production layout: hook = <workspace>/<plugin>/hooks/<hook>.py
      hook_relative = <plugin>/hooks/<hook>.py (doesn't start with 'hooks/')
      → plugin repo is the workspace root → return repo.
    - Dev layout: hook = <workspace>/hooks/<hook>.py
      hook_relative = hooks/<hook>.py (starts with 'hooks/')
      → workspace IS the repo → return workspace.
    """
    abs_hook = os.path.abspath(hook_file)
    parent = os.path.dirname(abs_hook)          # hooks/
    repo = os.path.dirname(parent)              # repo/
    workspace = os.path.dirname(repo)           # workspace/ (parent of repo)

    # Detect: is the workspace the repo? If the hook's relative path from
    # workspace starts with 'hooks/', the workspace IS the repo (dev layout).
    # Otherwise the plugin is a subdirectory of the workspace (production layout).
    hook_relative = os.path.relpath(abs_hook, workspace)
    if hook_relative.startswith("hooks/"):
        return workspace   # dev layout: workspace IS the repo
    return repo            # production layout: plugin is nested inside workspace


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
