from django.urls import path, re_path
from . import views

urlpatterns = [
    path("", views.home, name="home"),  # 메인 선택 화면
    path("api/llama/chat/", views.llama_chat, name="llama_chat"),
    path("anglangl/", views.redirect_to_service, {"key": "anglangl"}, name="anglangl"),
    path("anglangl/<path:path>/", views.redirect_to_service, {"key": "anglangl"}),
    path("listening/", views.redirect_to_service, {"key": "listening"}, name="listening"),
    path("listening/<path:path>/", views.redirect_to_service, {"key": "listening"}),
    path("movies/", views.redirect_to_service, {"key": "movies"}, name="movies"),
    path("movies/<path:path>/", views.redirect_to_service, {"key": "movies"}),
    path("address/", views.redirect_to_service, {"key": "address"}, name="address"),
    path("address/<path:path>/", views.redirect_to_service, {"key": "address"}),
    path("webdesign/", views.redirect_to_service, {"key": "webdesign"}, name="webdesign"),
    path("webdesign/<path:path>/", views.redirect_to_service, {"key": "webdesign"}),
    path("erp/", views.redirect_to_service, {"key": "erp"}, name="erp"),
    path("erp/<path:path>/", views.redirect_to_service, {"key": "erp"}),
    path("build/", views.redirect_to_service, {"key": "build"}, name="build"),
    path("build/<path:path>/", views.redirect_to_service, {"key": "build"}),
    path("stock/", views.redirect_to_service, {"key": "stock"}, name="stock"),
    path("stock/<path:path>/", views.redirect_to_service, {"key": "stock"}),
    path("art/", views.redirect_to_service, {"key": "art"}, name="art"),
    path("art/<path:path>/", views.redirect_to_service, {"key": "art"}),
    path("pet/", views.redirect_to_service, {"key": "pet"}, name="pet"),
    path("pet/<path:path>/", views.redirect_to_service, {"key": "pet"}),
    path("petlens/", views.redirect_to_service, {"key": "petlens"}, name="petlens"),
    path("petlens/<path:path>/", views.redirect_to_service, {"key": "petlens"}),
    path("shop/", views.redirect_to_service, {"key": "shop"}, name="shop"),
    path("shop/<path:path>/", views.redirect_to_service, {"key": "shop"}),
    path("thewiki/", views.redirect_to_service, {"key": "thewiki"}, name="thewiki"),
    path("thewiki/<path:path>/", views.redirect_to_service, {"key": "thewiki"}),
]
