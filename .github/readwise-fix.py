"""Apply the Readwise view test fixes to the fork's sync/v0.9.4 branch."""

import pathlib

TEMPLATE = "bookwyrm/templates/preferences/readwise.html"
TESTS = "bookwyrm/tests/views/preferences/test_readwise.py"

OLD_SETUP = '''    def setUp(self):
        """Individual test setup"""
        self.factory = RequestFactory()'''

NEW_SETUP = '''    def setUp(self):
        """Individual test setup"""
        self.factory = RequestFactory()

    def _request(self, method, data=None):
        """Build a request with message storage attached.

        Middleware doesn't run when a view is called directly, so views that
        add messages need storage set up by hand.
        """
        request = getattr(self.factory, method)("", data or {})
        request.user = self.local_user
        request._messages = CookieStorage(request)
        return request'''

OLD_POST = '''        request = self.factory.post(
            "",
            {
                "readwise_token": "new_test_token",
                "readwise_auto_export": True,
            },
        )
        request.user = self.local_user'''

NEW_POST = '''        request = self._request(
            "post",
            {
                "readwise_token": "new_test_token",
                "readwise_auto_export": True,
            },
        )'''

PATCHES = [
    (TEMPLATE, 'rel="noopener"', 'rel="nofollow noopener noreferrer"', 2),
    (
        TESTS,
        "from django.test import TestCase\nfrom django.test.client import RequestFactory",
        "from django.contrib.messages.storage.cookie import CookieStorage\n"
        "from django.test import TestCase\nfrom django.test.client import RequestFactory",
        1,
    ),
    (TESTS, OLD_SETUP, NEW_SETUP, 1),
    (
        TESTS,
        '        request = self.factory.get("")\n        request.user = self.local_user',
        '        request = self._request("get")',
        2,
    ),
    (TESTS, OLD_POST, NEW_POST, 1),
    (
        TESTS,
        '        request = self.factory.post("", {"action": "export"})\n        request.user = self.local_user',
        '        request = self._request("post", {"action": "export"})',
        2,
    ),
    (
        TESTS,
        '        request = self.factory.post("", {"action": "import"})\n        request.user = self.local_user',
        '        request = self._request("post", {"action": "import"})',
        2,
    ),
    (
        TESTS,
        '    def test_readwise_save_settings(self, *_):\n        """Test saving Readwise settings"""',
        '    @patch("bookwyrm.connectors.readwise.ReadwiseClient.validate_token")\n'
        '    def test_readwise_save_settings(self, mock_validate_token, *_):\n'
        '        """Test saving Readwise settings"""\n'
        '        mock_validate_token.return_value = True',
        1,
    ),
]

for path, old, new, expected in PATCHES:
    target = pathlib.Path(path)
    text = target.read_text()
    found = text.count(old)
    assert found == expected, f"{path}: expected {expected} matches, found {found}"
    target.write_text(text.replace(old, new))
    print(f"patched {path} ({expected})")
