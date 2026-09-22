from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Autenticação
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html"
        ),
        name="login",
    ),

    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    # Aplicações
    path("", include("clientes.urls")),
    path("", include("empresas.urls")),
    path("", include("vinculos.urls")),
    path("", include("calculos.urls")),
    path("", include("relatorios.urls")),
]