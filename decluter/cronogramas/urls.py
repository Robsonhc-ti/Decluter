from django.urls import path
from . import views

app_name = "cronogramas"

urlpatterns = [
    path("cronogramas/", views.lista_view, name="lista"),
    path("cronogramas/novo/", views.criar_view, name="criar"),
    path("cronogramas/<uuid:pk>/", views.detalhe_view, name="detalhe"),
]