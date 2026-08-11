from django.urls import path

from . import views

app_name = "empresas"

urlpatterns = [
    path("empresas/", views.lista, name="lista"),
    path("empresas/nova/", views.cadastrar, name="cadastrar"),
    path("empresas/<int:pk>/editar/", views.editar, name="editar"),
    path("empresas/<int:pk>/excluir/", views.excluir, name="excluir"),
]
