import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from .models import ServiceRuntimeStatus
from .services import get_service_operation


class ServiceControlError(RuntimeError):
    pass


@dataclass(frozen=True)
class ServiceRuntimeProbe:
    maintenance_enabled: bool
    backend_ready: bool
    backend_state: str
    message: str = ""

    @property
    def is_online(self):
        return self.backend_ready and not self.maintenance_enabled


def refresh_service_runtime(service):
    operation = get_service_operation(service.key)
    if not operation:
        return _mark_service_unsupported(service)

    probe = probe_service_runtime(operation)
    return _apply_probe(service, probe)


def control_service_runtime(service, target_online):
    operation = get_service_operation(service.key)
    if not operation:
        raise ServiceControlError("Operational control is not supported for this service.")

    service.target_online = target_online
    service.last_commanded_at = timezone.now()
    service.save(update_fields=["target_online", "last_commanded_at"])

    action = "maintenance-off" if target_online else "maintenance-on"
    command = _build_control_command(service.key, action)

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        service.runtime_status = ServiceRuntimeStatus.ERROR
        service.status_message = f"Failed to execute control command: {exc}"
        service.last_checked_at = timezone.now()
        service.save(update_fields=["runtime_status", "status_message", "last_checked_at"])
        raise ServiceControlError(service.status_message) from exc

    probe = _probe_from_control_output(service.key, result.stdout, result.stderr)
    refreshed = _apply_probe(service, probe)

    if result.returncode != 0:
        if refreshed.runtime_status in {
            ServiceRuntimeStatus.ONLINE,
            ServiceRuntimeStatus.MAINTENANCE,
        }:
            refreshed.runtime_status = ServiceRuntimeStatus.ERROR
        failure_message = result.stderr.strip() or probe.message or "Control command failed."
        refreshed.status_message = _join_messages(refreshed.status_message, failure_message)
        refreshed.save(update_fields=["runtime_status", "status_message"])
        raise ServiceControlError(refreshed.status_message)

    return refreshed


def probe_service_runtime(operation):
    marker = Path(operation["maintenance_marker"])
    unit_states = {
        unit: _read_unit_state(unit)
        for unit in operation["inspect_units"]
    }
    backend_ready = all(
        unit_states.get(unit) == "active"
        for unit in operation["required_active_units"]
    )
    backend_state = ", ".join(
        f"{unit}={state}"
        for unit, state in unit_states.items()
    )
    message = (
        f"maintenance={'on' if marker.exists() else 'off'}, {backend_state}"
        if backend_state
        else f"maintenance={'on' if marker.exists() else 'off'}"
    )
    return ServiceRuntimeProbe(
        maintenance_enabled=marker.exists(),
        backend_ready=backend_ready,
        backend_state=backend_state,
        message=message,
    )


def _mark_service_unsupported(service):
    service.is_online = False
    service.runtime_status = ServiceRuntimeStatus.UNSUPPORTED
    service.status_message = "Operational control is not configured for this service."
    service.last_checked_at = timezone.now()
    service.save(
        update_fields=["is_online", "runtime_status", "status_message", "last_checked_at"]
    )
    return service


def _read_unit_state(unit_name):
    result = subprocess.run(
        ["systemctl", "is-active", unit_name],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() or result.stderr.strip() or "unknown"


def _apply_probe(service, probe):
    service.is_online = probe.is_online
    service.runtime_status, service.status_message = _resolve_runtime_state(
        service.target_online,
        probe,
    )
    service.last_checked_at = timezone.now()
    service.save(
        update_fields=["is_online", "runtime_status", "status_message", "last_checked_at"]
    )
    return service


def _resolve_runtime_state(target_online, probe):
    issues = []
    if target_online:
        if probe.maintenance_enabled:
            issues.append("maintenance gate is still enabled")
        if not probe.backend_ready:
            issues.append(f"backend is not ready ({probe.backend_state})")
        if issues:
            return ServiceRuntimeStatus.MISMATCH, "; ".join(issues)
        return ServiceRuntimeStatus.ONLINE, probe.message

    if not probe.maintenance_enabled:
        issues.append("maintenance gate is not enabled")
    if probe.backend_ready:
        issues.append(f"backend is still ready ({probe.backend_state})")
    if issues:
        return ServiceRuntimeStatus.MISMATCH, "; ".join(issues)
    return ServiceRuntimeStatus.MAINTENANCE, probe.message


def _probe_from_control_output(service_key, stdout, stderr):
    payload = None
    try:
        payload = json.loads(stdout or "{}")
    except json.JSONDecodeError:
        payload = None

    if payload:
        return ServiceRuntimeProbe(
            maintenance_enabled=bool(payload.get("maintenance_enabled")),
            backend_ready=bool(payload.get("backend_ready")),
            backend_state=str(payload.get("backend_state") or "unknown"),
            message=str(payload.get("message") or "").strip(),
        )

    operation = get_service_operation(service_key)
    if not operation:
        return ServiceRuntimeProbe(False, False, "unsupported", stderr.strip())

    fallback = probe_service_runtime(operation)
    if stderr.strip():
        return ServiceRuntimeProbe(
            maintenance_enabled=fallback.maintenance_enabled,
            backend_ready=fallback.backend_ready,
            backend_state=fallback.backend_state,
            message=stderr.strip(),
        )
    return fallback


def _build_control_command(service_key, action):
    command = []
    if settings.THEHOME_SERVICE_CONTROL_USE_SUDO:
        command.extend(["sudo", "-n"])
    command.extend([settings.THEHOME_SERVICE_CONTROL_SCRIPT, service_key, action])
    return command


def _join_messages(left, right):
    if left and right:
        return f"{left} | {right}"
    return left or right
