from django.db import migrations

from home.services import DEFAULT_ACTIVE_KEYS, SERVICE_CATALOG


def seed_services(apps, schema_editor):
    Service = apps.get_model("home", "Service")
    for item in SERVICE_CATALOG:
        Service.objects.update_or_create(
            key=item["key"],
            defaults={
                "name": item["name"],
                "is_active": item["key"] in DEFAULT_ACTIVE_KEYS,
            },
        )


def unseed_services(apps, schema_editor):
    Service = apps.get_model("home", "Service")
    keys = [item["key"] for item in SERVICE_CATALOG]
    Service.objects.filter(key__in=keys).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_services, unseed_services),
    ]
