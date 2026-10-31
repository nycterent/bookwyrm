"""merge the fork migration graph with upstream v0.9.4"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("bookwyrm", "0232_v086_sync_merge"),
        ("bookwyrm", "0250_remove_series_user"),
    ]

    operations = []
