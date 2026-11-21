from django.db import migrations

from home.services import DEFAULT_ACTIVE_KEYS, SERVICE_CATALOG

NEW_KEYS = ["ticket", "ticketclassifier", "vector"]


def seed_services(apps, schema_editor):
    Service = apps.get_model("home", "Service")
    for item in SERVICE_CATALOG:
        if item["key"] not in NEW_KEYS:
            continue
        Service.objects.update_or_create(
            key=item["key"],
            defaults={
                "name": item["name"],
                "url": item["url"],
                "is_active": item["key"] in DEFAULT_ACTIVE_KEYS,
            },
        )


def unseed_services(apps, schema_editor):
    Service = apps.get_model("home", "Service")
    Service.objects.filter(key__in=NEW_KEYS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0005_service_url"),
    ]

    operations = [
        migrations.RunPython(seed_services, unseed_services),
    ]
