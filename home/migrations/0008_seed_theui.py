from django.db import migrations

from home.services import DEFAULT_ACTIVE_KEYS, SERVICE_CATALOG


SERVICE_KEY = "theui"


def seed_service(apps, schema_editor):
    Service = apps.get_model("home", "Service")
    item = next(entry for entry in SERVICE_CATALOG if entry["key"] == SERVICE_KEY)
    Service.objects.update_or_create(
        key=SERVICE_KEY,
        defaults={
            "name": item["name"],
            "url": item["url"],
            "is_active": SERVICE_KEY in DEFAULT_ACTIVE_KEYS,
        },
    )


def unseed_service(apps, schema_editor):
    Service = apps.get_model("home", "Service")
    Service.objects.filter(key=SERVICE_KEY).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0007_seed_requirement"),
    ]

    operations = [
        migrations.RunPython(seed_service, unseed_service),
    ]
