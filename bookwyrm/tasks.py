""" background tasks """

# For backward compatibility, provide app as a lazy property
class AppProxy:
    def __getattr__(self, name):
        # Lazy import to avoid circular imports
        from bookwyrm.celery_app import app as _app
        return getattr(_app, name)

app = AppProxy()

# priorities - for backwards compatibility, will be removed next release
LOW = "low_priority"
MEDIUM = "medium_priority"
HIGH = "high_priority"

STREAMS = "streams"
IMAGES = "images"
SUGGESTED_USERS = "suggested_users"
EMAIL = "email"
CONNECTORS = "connectors"
LISTS = "lists"
INBOX = "inbox"
IMPORTS = "imports"
IMPORT_TRIGGERED = "import_triggered"
BROADCAST = "broadcast"
MISC = "misc"
