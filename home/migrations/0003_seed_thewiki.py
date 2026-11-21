from django.db import migrations

from home.services import DEFAULT_ACTIVE_KEYS, SERVICE_CATALOG

NEW_KEY = "thewiki"


def seed_thewiki(apps, schema_editor):
    Service = apps.get_model("home", "Service")
    item = next(entry for entry in SERVICE_CATALOG if entry["key"] == NEW_KEY)
    Service.objects.update_or_create(
        key=item["key"],
        defaults={
            "name": item["name"],
            "is_active": item["key"] in DEFAULT_ACTIVE_KEYS,
        },
    )


def unseed_thewiki(apps, schema_editor):
    Service = apps.get_model("home", "Service")
    Service.objects.filter(key=NEW_KEY).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0002_seed_services"),
    ]

    operations = [
        migrations.RunPython(seed_thewiki, unseed_thewiki),
    ]
