from django.contrib import admin
from django.urls import path

from core import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("admin/", admin.site.urls),
]
