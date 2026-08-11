from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("clientes.urls")),
    path("", include("empresas.urls")),
    path("", include("vinculos.urls")),
    path("", include("calculos.urls")),
    path("", include("relatorios.urls")),
]
