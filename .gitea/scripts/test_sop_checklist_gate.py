import importlib.util
import pathlib
import unittest
from unittest import mock


SCRIPT_PATH = pathlib.Path(__file__).with_name("sop-checklist-gate.py")
SPEC = importlib.util.spec_from_file_location("sop_checklist_gate", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
sop_checklist_gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sop_checklist_gate)


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return b"{}"

    def getcode(self):
        return 200


class GiteaClientTest(unittest.TestCase):
    def test_request_uses_cloudflare_compatible_user_agent(self):
        requests = []

        def fake_urlopen(request, timeout):
            requests.append(request)
            return _Response()

        client = sop_checklist_gate.GiteaClient("git.moleculesai.app", "test-token")
        with mock.patch.object(
            sop_checklist_gate.urllib.request,
            "urlopen",
            side_effect=fake_urlopen,
        ):
            code, data = client._req("GET", "/version")

        self.assertEqual(code, 200)
        self.assertEqual(data, {})
        self.assertEqual(requests[0].get_header("User-agent"), "curl/8.4.0")


if __name__ == "__main__":
    unittest.main()
