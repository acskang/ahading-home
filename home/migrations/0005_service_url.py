from django.db import migrations, models

from home.models import validate_service_url
from home.services import SERVICE_CATALOG


def seed_url(apps, schema_editor):
    Service = apps.get_model("home", "Service")
    for item in SERVICE_CATALOG:
        Service.objects.filter(key=item["key"]).update(url=item["url"])


def unseed_url(apps, schema_editor):
    Service = apps.get_model("home", "Service")
    Service.objects.update(url="")


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0004_service_is_online_service_last_checked_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="url",
            field=models.CharField(blank=True, max_length=500, validators=[validate_service_url]),
        ),
        migrations.RunPython(seed_url, unseed_url),
    ]
