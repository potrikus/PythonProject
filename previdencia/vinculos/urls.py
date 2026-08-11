from django.urls import path

from . import views

app_name = "vinculos"

urlpatterns = [
    path("vinculos/", views.lista, name="lista"),
    path("vinculos/novo/", views.cadastrar, name="cadastrar"),
    path("vinculos/<int:pk>/editar/", views.editar, name="editar"),
    path("vinculos/<int:pk>/excluir/", views.excluir, name="excluir"),
]
