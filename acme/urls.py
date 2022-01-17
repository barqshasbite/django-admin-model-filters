# coding=utf-8

"""Project URL's."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
]

if "grappelli" in settings.INSTALLED_APPS:
    urlpatterns.insert(
        0,
        path("grappelli/", include("grappelli.urls")),
    )
