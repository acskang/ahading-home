from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Service
from .service_runtime import ServiceControlError, control_service_runtime, refresh_service_runtime
from .services import get_service_operation


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "key",
        "url",
        "is_active",
        "public_state_badge",
        "runtime_controls",
    )
    list_editable = ("url", "is_active")
    search_fields = ("name", "key", "url")
    readonly_fields = (
        "key",
        "name",
        "runtime_summary",
        "status_message",
        "last_checked_at",
        "last_commanded_at",
        "runtime_controls_detail",
    )
    fields = (
        "name",
        "key",
        "url",
        "is_active",
        "runtime_summary",
        "status_message",
        "last_checked_at",
        "last_commanded_at",
        "runtime_controls_detail",
    )

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        custom_urls = [
            path(
                "<path:object_id>/refresh-runtime/",
                self.admin_site.admin_view(self.refresh_runtime_view),
                name="home_service_refresh_runtime",
            ),
            path(
                "<path:object_id>/runtime-control/<str:target>/",
                self.admin_site.admin_view(self.runtime_control_view),
                name="home_service_runtime_control",
            ),
        ]
        return custom_urls + super().get_urls()

    @admin.display(description="공개 상태")
    def public_state_badge(self, obj):
        label = self._public_state_label(obj)
        palette = {
            "online": "#1ea672",
            "maintenance": "#d06a1a",
            "mismatch": "#d18b00",
            "error": "#b33a3a",
            "unsupported": "#6b7280",
            "unknown": "#6b7280",
        }
        return format_html(
            '<strong style="color:{};" title="{}">{}</strong>',
            palette.get(obj.runtime_status, "#6b7280"),
            obj.status_message or label,
            label,
        )

    @admin.display(description="운영 제어")
    def runtime_controls(self, obj):
        refresh_url = reverse("admin:home_service_refresh_runtime", args=[obj.pk])
        refresh_link = format_html('<a class="button" href="{}">상태확인</a>', refresh_url)
        if not get_service_operation(obj.key):
            return format_html(
                '{} <span style="color:#6b7280;">운영 제어 미지원</span>',
                refresh_link,
            )

        action_target = "maintenance" if obj.target_online else "online"
        action_label = "유지보수 전환" if obj.target_online else "온라인 복구"
        action_url = reverse("admin:home_service_runtime_control", args=[obj.pk, action_target])
        return format_html(
            '{} <a class="button" href="{}">{}</a>',
            refresh_link,
            action_url,
            action_label,
        )

    @admin.display(description="운영 제어")
    def runtime_controls_detail(self, obj):
        return self.runtime_controls(obj)

    @admin.display(description="운영 상태")
    def runtime_summary(self, obj):
        return format_html(
            "<strong>{}</strong><br><span style='color:#6b7280;'>목표: {} / 실제 공개: {}</span>",
            self._public_state_label(obj),
            "온라인" if obj.target_online else "유지보수",
            "예" if obj.is_online else "아니오",
        )

    def refresh_runtime_view(self, request, object_id):
        service = get_object_or_404(Service, pk=object_id)
        refresh_service_runtime(service)
        self.message_user(
            request,
            f"{service.name} runtime status refreshed: {service.get_runtime_status_display()}",
            level=messages.INFO,
        )
        return redirect("admin:home_service_changelist")

    def runtime_control_view(self, request, object_id, target):
        service = get_object_or_404(Service, pk=object_id)
        if not get_service_operation(service.key):
            self.message_user(
                request,
                "Operational control is not supported for this service.",
                level=messages.ERROR,
            )
            return redirect("admin:home_service_changelist")

        target_online = target == "online"
        if target not in {"online", "maintenance"}:
            self.message_user(request, "Unknown runtime control target.", level=messages.ERROR)
            return redirect("admin:home_service_changelist")

        if request.method == "POST":
            try:
                control_service_runtime(service, target_online=target_online)
            except ServiceControlError as exc:
                self.message_user(request, str(exc), level=messages.ERROR)
            else:
                self.message_user(
                    request,
                    f"{service.name} target updated to {'online' if target_online else 'maintenance'}.",
                    level=messages.SUCCESS,
                )
            return redirect("admin:home_service_changelist")

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "service": service,
            "target_online": target_online,
            "title": f"Confirm runtime control for {service.name}",
        }
        return TemplateResponse(request, "admin/home/service/control_confirm.html", context)

    def _public_state_label(self, obj):
        labels = {
            "online": "운영중",
            "maintenance": "점검중",
            "mismatch": "불일치",
            "error": "오류",
            "unsupported": "미지원",
            "unknown": "미확인",
        }
        return labels.get(obj.runtime_status, obj.get_runtime_status_display())
