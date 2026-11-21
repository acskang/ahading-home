import json

import requests
from django.conf import settings
from django.http import Http404, JsonResponse, HttpResponse, HttpResponsePermanentRedirect
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .llama_chat import LlamaChatServiceError, LlamaChatValidationError, build_chat_response
from .models import Service
from .services import SERVICE_CATALOG


def home(request):
    services_by_key = {service.key: service for service in Service.objects.all()}
    services = []
    for item in SERVICE_CATALOG:
        service = services_by_key.get(item["key"])
        services.append({
            **item,
            "is_active": service.is_active if service else False,
            "url": service.url if service and service.url else item["url"],
        })
    return render(
        request,
        "home.html",
        {
            "services": services,
            "chat_widget_enabled": getattr(settings, "CHAT_WIDGET_ENABLED", True),
        },
    )


@require_POST
def llama_chat(request):
    if not getattr(settings, "CHAT_WIDGET_ENABLED", True):
        return JsonResponse(
            {"ok": False, "error": "AI 채팅 기능이 현재 비활성화되어 있습니다."},
            status=503,
        )
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON payload."}, status=400)
    try:
        result = build_chat_response(
            message=body.get("message"),
            history=body.get("history", []),
        )
    except LlamaChatValidationError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
    except LlamaChatServiceError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=503)
    except Exception:
        return JsonResponse(
            {"ok": False, "error": "지금은 AI 챗봇 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요."},
            status=503,
        )
    return JsonResponse(result)


def _build_redirect_target(request, base_url, path=""):
    target = base_url
    if path:
        target = f"{base_url}{path}"
        if request.path.endswith("/") and not target.endswith("/"):
            target = f"{target}/"
    query_string = request.META.get("QUERY_STRING")
    if query_string:
        target = f"{target}?{query_string}"
    return target


def redirect_to_service(request, key, path=""):
    try:
        base_url = Service.objects.get(key=key).url
    except Service.DoesNotExist:
        base_url = ""
    if not base_url:
        base_url = next(
            (item["url"] for item in SERVICE_CATALOG if item["key"] == key),
            "",
        )
    if not base_url:
        raise Http404(f"No redirect target configured for service '{key}'.")
    target = _build_redirect_target(request, base_url, path)
    return HttpResponsePermanentRedirect(target)


def proxy_to_backend(request, path):
    # URL에서 서비스 구분
    service_map = {
        "listening": "http://localhost:8001",
        "movies": "http://localhost:8002",
    }

    service = request.path.split("/")[1]
    backend_url = f"{service_map[service]}/{path}"

    response = requests.request(
        method=request.method,
        url=backend_url,
        headers={key: value for key, value in request.headers.items() if key != "Host"},
        data=request.body,
        cookies=request.COOKIES,
        allow_redirects=False,
    )

    return HttpResponse(response.content, status=response.status_code)
