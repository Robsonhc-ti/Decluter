from django.urls import path
from . import views

app_name = "projetos"

urlpatterns = [
    path("projetos/", views.lista_view, name="lista"),
    path("projetos/novo/", views.criar_view, name="criar"),
]