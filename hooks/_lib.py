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
    the naive dirname chain overshoots by one level, so we detect this by
    checking whether the resolved workspace contains a 'hooks/' subdirectory.

    - Normal layout (plugin installed in workspace): repo = <workspace>/<plugin>/.
      workspace = <workspace>/. If workspace has hooks/, we've walked too far
      and the actual repo is one level deeper → return repo.
    - Dev layout (plugin checked out directly): repo = workspace.
      workspace = parent-of-repo, which lacks hooks/ → workspace is right.
    """
    abs_hook = os.path.abspath(hook_file)
    parent = os.path.dirname(abs_hook)          # hooks/
    repo = os.path.dirname(parent)              # repo/
    workspace = os.path.dirname(repo)           # workspace/ (parent of repo)

    # Detect overshoot by checking whether the resolved workspace contains
    # a 'hooks/' subdirectory. In a normal install, the workspace is the parent
    # of the plugin repo and has no hooks/; finding one means we walked too far.
    # In a dev layout, workspace is the parent of the repo (no hooks/) → correct.
    if os.path.isdir(os.path.join(workspace, "hooks")):
        # Overshot: workspace is actually the parent; the repo is one level deeper.
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
