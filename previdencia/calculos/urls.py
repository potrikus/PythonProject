from django.urls import path

from . import views

app_name = "calculos"

urlpatterns = [
    path("calculos/", views.lista, name="lista"),
    path("calculos/nova/", views.nova, name="nova"),
    path("calculos/<int:pk>/", views.detalhe, name="detalhe"),
]
