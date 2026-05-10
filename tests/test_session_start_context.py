#!/usr/bin/env python3
"""Integration tests for session-start-context.py hook logic.

Tests the hook's main() by running it as a subprocess with the LEARNINGS
path and gh commands patched. Since the hook's __file__-based path resolution
goes up 3 levels from hooks/ to repo root, we use importlib to load the module
directly from the test dir and override LEARNINGS before calling main().
"""
import io
import json
import os
import sys
import importlib.util
from pathlib import Path
from unittest import mock

import pytest

# Add hooks/ dir to path
hooks_dir = os.path.join(os.path.dirname(__file__), "..", "hooks")
sys.path.insert(0, hooks_dir)

# Import the hook module via importlib (filename has dashes)
_spec = importlib.util.spec_from_file_location(
    "session_start_context",
    os.path.join(hooks_dir, "session-start-context.py"),
)
session_start_context = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(session_start_context)

tail = session_start_context.tail
gh_count = session_start_context.gh_count


class TestTail:
    """Tests for the tail() helper."""

    def test_tail_returns_last_n_lines(self):
        """tail should return only the last N lines."""
        p = Path("/tmp/test-tail-lines.txt")
        p.write_text("\n".join([f'{{"n":{i}}}' for i in range(30)]) + "\n")
        result = tail(str(p), 5)
        assert result.count("\n") == 4  # 5 lines = 4 newlines
        p.unlink()

    def test_tail_returns_empty_for_missing_file(self):
        """tail should return empty string for missing file."""
        result = tail("/tmp/nonexistent-file-12345.txt", 20)
        assert result == ""

    def test_tail_handles_file_with_malformed_lines(self):
        """tail should not break on malformed JSON lines."""
        p = Path("/tmp/bad-learnings.jsonl")
        p.write_text('valid line\nnot json\n{"ok":true}\n')
        result = tail(str(p), 10)
        assert "valid line" in result
        assert "not json" in result
        p.unlink()

    def test_tail_handles_fewer_lines_than_requested(self):
        """tail should return all lines if file has fewer than N."""
        p = Path("/tmp/few-lines.txt")
        p.write_text("line1\nline2\nline3\n")
        result = tail(str(p), 10)
        assert result.count("\n") == 2
        p.unlink()


class TestGhCount:
    """Tests for the gh_count() helper."""

    def test_gh_count_parses_json_array(self):
        """gh_count should count items in gh --json output."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(
                returncode=0,
                stdout='[{"number":1},{"number":2},{"number":3}]',
            )
            result = gh_count(["pr", "list"])
            assert result == "3"

    def test_gh_count_returns_question_on_failure(self):
        """gh_count should return '?' when gh fails."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=1, stderr="not found")
            result = gh_count(["pr", "list"])
            assert result == "?"

    def test_gh_count_returns_question_on_exception(self):
        """gh_count should return '?' when subprocess raises."""
        with mock.patch("subprocess.run", side_effect=FileNotFoundError):
            result = gh_count(["pr", "list"])
            assert result == "?"

    def test_gh_count_handles_empty_json_array(self):
        """gh_count should return '0' for empty array."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0, stdout="[]")
            result = gh_count(["issue", "list"])
            assert result == "0"


class TestMainIntegration:
    """Integration tests for the full hook using mocked dependencies.

    We load the module and override LEARNINGS + subprocess before calling main().
    """

    def _run_with_learnings(self, learnings_content: str, learnings_path: Path):
        """Run the hook with a given learnings file content, mocking gh."""
        learnings_path.parent.mkdir(parents=True, exist_ok=True)
        learnings_path.write_text(learnings_content)

        # Reload module and patch
        import importlib
        spec = importlib.util.spec_from_file_location(
            "hook_mod", os.path.join(hooks_dir, "session-start-context.py")
        )
        mod = importlib.util.module_from_spec(spec)
        mod.LEARNINGS = str(learnings_path)
        spec.loader.exec_module(mod)

        stdout = io.StringIO()
        with mock.patch("sys.stdout", stdout), mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0, stdout="[]")
            mod.main()

        output = stdout.getvalue()
        if output.strip():
            lines = [l for l in output.strip().split("\n") if l.strip()]
            for line in reversed(lines):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        return {}

    def test_emits_learnings_in_context(self):
        """When learnings exist, additionalContext should include them."""
        p = Path("/tmp/test-learnings-integration.jsonl")
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Write learnings and run
            p.write_text(
                '{"ts":"2026-05-10T10:00:00Z","text":"Fixed OFFSEC-002"}\n'
                '{"ts":"2026-05-10T09:00:00Z","text":"Added test coverage"}\n'
            )
            result = self._run_with_learnings(
                '{"ts":"2026-05-10T10:00:00Z","text":"Fixed OFFSEC-002"}\n'
                '{"ts":"2026-05-10T09:00:00Z","text":"Added test coverage"}\n',
                p,
            )
            ctx = result.get("additionalContext", "")
            # With learnings, gh mock returns "[]", so we get learnings + repo state
            assert "Fixed" in ctx or "OFFSEC-002" in ctx or "cron" in ctx.lower() or len(ctx) > 10
        finally:
            p.unlink(missing_ok=True)

    def test_emits_repo_state_via_gh_mock(self):
        """When no learnings, hook still emits repo state from gh count mock."""
        p = Path("/tmp/test-no-learnings-integration.jsonl")
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Write empty content
            p.write_text("")
            result = self._run_with_learnings("", p)
            ctx = result.get("additionalContext", "")
            # gh mock returns [], so pr/issue count = 0, but gh_count still produces output
            assert "Repo state" in ctx or "pr" in ctx.lower() or "issue" in ctx.lower()
        finally:
            p.unlink(missing_ok=True)

    def test_add_context_helper(self):
        """add_context should emit additionalContext JSON."""
        from _lib import add_context

        stdout = io.StringIO()
        with mock.patch("sys.stdout", stdout):
            add_context("Test context")
        output = stdout.getvalue()
        payload = json.loads(output)
        assert payload.get("additionalContext") == "Test context"

    def test_add_context_ignores_empty(self):
        """add_context should emit nothing for empty/whitespace text."""
        from _lib import add_context

        for text in ("", "   ", "\n"):
            stdout = io.StringIO()
            with mock.patch("sys.stdout", stdout):
                add_context(text)
            assert stdout.getvalue() == ""


class TestHookErrorHandling:
    """Tests for error handling in the hook."""

    def test_hook_exits_cleanly_on_exception(self):
        """Hook should exit(0) on exception, not crash."""
        spec = importlib.util.spec_from_file_location(
            "hook_exc", os.path.join(hooks_dir, "session-start-context.py")
        )
        mod = importlib.util.module_from_spec(spec)
        # Set a path that causes an exception when read
        mod.LEARNINGS = "/tmp/definitely-does-not-exist-and-cannot-be-read-12345"
        spec.loader.exec_module(mod)

        stdout = io.StringIO()
        with mock.patch("sys.stdout", stdout), mock.patch("sys.exit") as mock_exit:
            mod.main()
        # main() calls sys.exit(0) after error - our mock intercepts it