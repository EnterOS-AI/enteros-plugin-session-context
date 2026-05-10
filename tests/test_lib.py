#!/usr/bin/env python3
"""Unit tests for session-start-context.py hook."""
import io
import json
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

# Add hooks/ dir to path so _lib imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))


class TestDenyPreToolUse:
    """Tests for deny_pretooluse helper (imported from _lib)."""

    def test_deny_emits_json_permission_denied(self):
        """deny_pretooluse should emit JSON with permissionDecision: deny."""
        from _lib import deny_pretooluse

        stdout = io.StringIO()
        with mock.patch("sys.stdout", stdout), mock.patch("sys.exit") as exit_mock:
            deny_pretooluse("test reason")
        output = stdout.getvalue()
        payload = json.loads(output)
        assert (
            payload.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
        )
        assert "test reason" in str(payload)


class TestReadInput:
    """Tests for read_input helper (imported from _lib)."""

    def test_parses_valid_json(self):
        """read_input should parse valid Claude Code hook JSON from stdin."""
        from _lib import read_input

        stdin = io.StringIO('{"tool_input": {"file_path": "src/main.py"}}')
        with mock.patch("sys.stdin", stdin):
            result = read_input()
        assert result["tool_input"]["file_path"] == "src/main.py"

    def test_empty_stdin_returns_empty_dict(self):
        """read_input with empty stdin should return an empty dict."""
        from _lib import read_input

        with mock.patch("sys.stdin", io.StringIO("")):
            result = read_input()
        assert result == {}

    def test_malformed_json_returns_empty_dict(self):
        """read_input with invalid JSON should return empty dict, not raise."""
        from _lib import read_input

        with mock.patch("sys.stdin", io.StringIO("not valid json")):
            result = read_input()
        assert result == {}


class TestEmit:
    """Tests for emit helper (imported from _lib)."""

    def test_emit_prints_json_to_stdout(self):
        """emit should print a JSON-encoded dict to stdout."""
        from _lib import emit

        stdout = io.StringIO()
        with mock.patch("sys.stdout", stdout):
            emit({"foo": "bar"})
        output = stdout.getvalue()
        assert json.loads(output) == {"foo": "bar"}


class TestWarnToStderr:
    """Tests for warn_to_stderr (imported from _lib)."""

    def test_warn_to_stderr_writes_to_stderr(self):
        """warn_to_stderr should write to stderr."""
        from _lib import warn_to_stderr

        stderr = io.StringIO()
        with mock.patch("sys.stderr", stderr):
            warn_to_stderr("warning message")
        assert "warning message" in stderr.getvalue()


class TestAddContext:
    """Tests for add_context helper (imported from _lib)."""

    def test_add_context_emits_additional_context(self):
        """add_context should emit additionalContext field."""
        from _lib import add_context

        stdout = io.StringIO()
        with mock.patch("sys.stdout", stdout):
            add_context("Some context text")
        output = stdout.getvalue()
        payload = json.loads(output)
        assert payload.get("additionalContext") == "Some context text"

    def test_add_context_ignores_empty_text(self):
        """add_context should emit nothing when text is empty."""
        from _lib import add_context

        stdout = io.StringIO()
        with mock.patch("sys.stdout", stdout):
            add_context("")
        assert stdout.getvalue() == ""

        stdout2 = io.StringIO()
        with mock.patch("sys.stdout", stdout2):
            add_context("   ")
        assert stdout2.getvalue() == ""


class TestGetRepoRoot:
    """Tests for get_repo_root helper (imported from _lib)."""

    def test_workspace_has_hooks_returns_repo(self):
        """When workspace has hooks/ (production install), return the plugin repo."""
        from _lib import get_repo_root

        # Production: hook at <plugin-repo>/hooks/hook.py, workspace = parent-of-plugin-repo
        # /tmp/my-repo/hooks/hook.py → parent=/tmp/my-repo/hooks, repo=/tmp/my-repo, workspace=/tmp
        # The function checks isdir(workspace + "/hooks") = isdir("/tmp/hooks")
        with mock.patch("os.path.isdir", return_value=True):
            result = get_repo_root("/tmp/my-repo/hooks/session-start-context.py")
            # True → overshot → return repo
            assert result == "/tmp/my-repo"

    def test_workspace_lacks_hooks_returns_workspace(self):
        """When workspace lacks hooks/ (dev layout), workspace IS the repo root."""
        from _lib import get_repo_root

        with mock.patch("os.path.isdir", return_value=False):
            result = get_repo_root("/tmp/my-repo/hooks/session-start-context.py")
            # False → no overshoot → return workspace
            assert result == "/tmp"

    def test_real_repo_path_in_this_repo(self):
        """Verify get_repo_root on the actual repo resolves to a valid root."""
        from _lib import get_repo_root

        # This test file is at: <repo>/tests/test_lib.py
        # The hook is at: <repo>/hooks/session-start-context.py
        hooks_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hooks")
        hook_file = os.path.join(hooks_dir, "session-start-context.py")
        result = get_repo_root(hook_file)
        # Sanity: result is an absolute path
        assert os.path.isabs(result), f"result {result!r} is not absolute"
        # The result is the workspace (if installed) or repo (if dev layout).
        # Either way the hook file is inside it.
        assert os.path.isdir(result), f"result {result!r} is not a directory"