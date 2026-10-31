"""Apply the remaining test fixes to the fork's sync/v0.9.4 branch."""

import pathlib

USER = "bookwyrm/tests/views/test_user.py"
SHELF = "bookwyrm/tests/views/shelf/test_shelf.py"
STATS = "bookwyrm/tests/views/admin/test_instance_stats.py"
BACKOFF = "bookwyrm/tests/connectors/test_connector_backoff.py"

PATCHES = [
    (
        USER,
        '            result = view(request, "mouse")',
        '            result = view(request, username="mouse")',
        1,
    ),
    (
        USER,
        '            result = view(request, "nutria@example.com")',
        '            result = view(request, username="nutria@example.com")',
        1,
    ),
    (
        SHELF,
        '            result = view(request, "nutria@example.com", remote_shelf.identifier)',
        '            result = view(\n'
        '                request,\n'
        '                username="nutria@example.com",\n'
        '                shelf_identifier=remote_shelf.identifier,\n'
        '            )',
        1,
    ),
    (
        STATS,
        '        from django.utils import timezone\n'
        '        from bookwyrm.views.admin.instance_stats import get_activity_stats',
        '        import json\n\n'
        '        from django.utils import timezone\n'
        '        from bookwyrm.views.admin.instance_stats import get_activity_stats',
        1,
    ),
    (
        STATS,
        '        self.assertEqual(len(activity["labels"]), 7)\n'
        '        self.assertEqual(len(activity["status_by_day"]), 7)',
        '        # the series are JSON-encoded for the JavaScript chart\n'
        '        self.assertEqual(len(json.loads(activity["labels"])), 7)\n'
        '        self.assertEqual(len(json.loads(activity["status_by_day"])), 7)',
        1,
    ),
    (
        BACKOFF,
        '        stats = ConnectorBackoff.get_health_stats(self.connector_id)\n'
        '        # 7/11 = 63.6% < 70% = degraded\n'
        '        self.assertEqual(stats["health_status"], "degraded")',
        '        # being in backoff also reports unavailable, so clear that state to\n'
        '        # isolate the success-rate threshold this test covers\n'
        '        cache.delete(ConnectorBackoff._get_cache_key(self.connector_id))\n\n'
        '        stats = ConnectorBackoff.get_health_stats(self.connector_id)\n'
        '        # 7/11 = 63.6% < 70% = degraded\n'
        '        self.assertEqual(stats["health_status"], "degraded")',
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
