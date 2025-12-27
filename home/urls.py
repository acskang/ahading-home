from django.urls import path, re_path
from . import views

urlpatterns = [
    path("", views.home, name="home"),  # 메인 선택 화면
    path("listening/", views.redirect_to_listening, name="listening"),
    path("listening/<path:path>/", views.redirect_to_listening),
    path("movies/", views.redirect_to_movies, name="movies"),
    path("movies/<path:path>/", views.redirect_to_movies),
    path("address/", views.redirect_to_address, name="address"),
    path("address/<path:path>/", views.redirect_to_address),
]
