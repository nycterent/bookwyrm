"""Apply the remaining CI fixes to the fork's sync/v0.9.4 branch."""

import pathlib

OLD_ERROR_BLOCK = '''    except requests.HTTPError as e:
        if (
            hasattr(e, "response")
            and hasattr(e.response, "status_code")
            and e.response.status_code in (401, 404, 410)
        ):
            # 401/404/410 are expected - private accounts, deleted/gone resources
            logger.info(
                "Remote resource unavailable (%s) - remote_id: %s",
                e.response.status_code,
                remote_id,
            )
        else:
            # Other HTTP errors - log but don't report to Sentry
            logger.warning("HTTP error - remote_id: %s - error: %s", remote_id, e)
        # Record failure for backoff tracking
        RemoteInstanceBackoff.record_failure(remote_id)
        return None
'''

NEW_ERROR_BLOCK = '''    except requests.HTTPError as e:
        status_code = getattr(getattr(e, "response", None), "status_code", None)
        if status_code == 410:
            # gone for good - backing off and retrying it would be pointless
            logger.warning(
                "request for object dropped because it is gone (410) - remote_id: %s",
                remote_id,
            )
            return None
        if status_code in (401, 404):
            # expected - private accounts, deleted resources
            logger.info(
                "Remote resource unavailable (%s) - remote_id: %s",
                status_code,
                remote_id,
            )
        else:
            # Other HTTP errors - log but don't report to Sentry
            logger.warning("HTTP error - remote_id: %s - error: %s", remote_id, e)
        # Record failure for backoff tracking
        RemoteInstanceBackoff.record_failure(remote_id)
        return None
'''

OLD_IMPORT = 'from django.test import TestCase\nfrom django.core.cache import cache'
NEW_IMPORT = 'from django.test import TestCase, override_settings\nfrom django.core.cache import cache'

OLD_CLASS = 'class TestConnectorBackoff(TestCase):\n    """Test the ConnectorBackoff class"""'
NEW_CLASS = 'x'

LOCMEM = '''# these tests exercise cache-backed state, so they need a real cache rather
# than the dummy cache the test settings default to
LOCMEM_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
    "file_resubmit": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "/tmp/file_resubmit_tests/",
    },
}


'''

NEW_CLASS = (
    LOCMEM
    + '@override_settings(CACHES=LOCMEM_CACHES)\n'
    + 'class TestConnectorBackoff(TestCase):\n    """Test the ConnectorBackoff class"""'
)

OLD_SYNC = 'class TestSyncConnectorHealth(TestCase):\n    """Test the Celery task for syncing health"""'
NEW_SYNC = (
    '@override_settings(CACHES=LOCMEM_CACHES)\n'
    + 'class TestSyncConnectorHealth(TestCase):\n    """Test the Celery task for syncing health"""'
)

PATCHES = [
    ("bookwyrm/activitypub/base_activity.py", OLD_ERROR_BLOCK, NEW_ERROR_BLOCK),
    ("bookwyrm/tests/connectors/test_connector_backoff.py", OLD_IMPORT, NEW_IMPORT),
    ("bookwyrm/tests/connectors/test_connector_backoff.py", OLD_CLASS, NEW_CLASS),
    ("bookwyrm/tests/connectors/test_connector_backoff.py", OLD_SYNC, NEW_SYNC),
]

for path, old, new in PATCHES:
    target = pathlib.Path(path)
    text = target.read_text()
    found = text.count(old)
    assert found == 1, f"{path}: expected 1 match, found {found}"
    target.write_text(text.replace(old, new, 1))
    print(f"patched {path}")
