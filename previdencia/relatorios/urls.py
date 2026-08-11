from django.urls import path

from . import views


app_name = "relatorios"


urlpatterns = [
    path("relatorios/", views.lista, name="lista"),
    path(
        "relatorios/previdenciario/<int:pk>/",
        views.previdenciario,
        name="previdenciario",
    ),
]