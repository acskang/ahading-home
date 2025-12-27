import requests
from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.shortcuts import render


def home(request):
    return render(request, "home.html")


def redirect_to_address(request, path=""):
    base_url = "http://address.thesysm.com/"
    target = base_url
    if path:
        target = f"{base_url}{path}"
    query_string = request.META.get("QUERY_STRING")
    if query_string:
        target = f"{target}?{query_string}"
    return HttpResponsePermanentRedirect(target)


def redirect_to_movies(request, path=""):
    base_url = "http://movies.thesysm.com/"
    target = base_url
    if path:
        target = f"{base_url}{path}"
    query_string = request.META.get("QUERY_STRING")
    if query_string:
        target = f"{target}?{query_string}"
    return HttpResponsePermanentRedirect(target)


def redirect_to_listening(request, path=""):
    base_url = "http://listening.thesysm.com/"
    target = base_url
    if path:
        target = f"{base_url}{path}"
    query_string = request.META.get("QUERY_STRING")
    if query_string:
        target = f"{target}?{query_string}"
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
