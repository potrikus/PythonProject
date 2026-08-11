from django.urls import path
from . import views

app_name = "clientes"

urlpatterns = [
    path("", views.home, name="home"),
    path("clientes/", views.lista, name="lista"),
    path("clientes/novo/", views.cadastrar, name="cadastrar"),
    path("clientes/<int:pk>/editar/", views.editar, name="editar"),
    path("clientes/<int:pk>/excluir/", views.excluir, name="excluir"),
]
