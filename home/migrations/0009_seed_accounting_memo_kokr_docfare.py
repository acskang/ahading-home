from django.db import migrations

from home.services import DEFAULT_ACTIVE_KEYS, SERVICE_CATALOG


SERVICE_KEYS = ["accounting", "memo", "kokr", "docfare"]


def seed_service(apps, schema_editor):
    Service = apps.get_model("home", "Service")
    for key in SERVICE_KEYS:
        item = next(entry for entry in SERVICE_CATALOG if entry["key"] == key)
        Service.objects.update_or_create(
            key=key,
            defaults={
                "name": item["name"],
                "url": item["url"],
                "is_active": key in DEFAULT_ACTIVE_KEYS,
            },
        )


def unseed_service(apps, schema_editor):
    Service = apps.get_model("home", "Service")
    Service.objects.filter(key__in=SERVICE_KEYS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0008_seed_theui"),
    ]

    operations = [
        migrations.RunPython(seed_service, unseed_service),
    ]
