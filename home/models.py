from django.core.exceptions import ValidationError
from django.db import models


def validate_service_url(value):
    if not (value.startswith("http://") or value.startswith("https://") or value.startswith("/")):
        raise ValidationError("URL must start with http://, https://, or /.")


class ServiceRuntimeStatus(models.TextChoices):
    UNKNOWN = "unknown", "Unknown"
    ONLINE = "online", "Online"
    MAINTENANCE = "maintenance", "Maintenance"
    MISMATCH = "mismatch", "Mismatch"
    ERROR = "error", "Error"
    UNSUPPORTED = "unsupported", "Unsupported"


class Service(models.Model):
    key = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=500, blank=True, validators=[validate_service_url])
    is_active = models.BooleanField(default=False)
    target_online = models.BooleanField(default=True)
    is_online = models.BooleanField(default=False)
    runtime_status = models.CharField(
        max_length=20,
        choices=ServiceRuntimeStatus.choices,
        default=ServiceRuntimeStatus.UNKNOWN,
    )
    status_message = models.CharField(max_length=255, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_commanded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return self.name
