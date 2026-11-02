from django.urls import path
from . import views

app_name = "cronogramas"

urlpatterns = [
    path("cronogramas/", views.lista_view, name="lista"),
    path("cronogramas/novo/", views.criar_view, name="criar"),
    path("cronogramas/novo/faculdade/", views.criar_faculdade_view, name="criar_faculdade"),
    path("cronogramas/novo/enem/", views.criar_enem_view, name="criar_enem"),
    path("cronogramas/sugestoes/", views.sugestoes_view, name="sugestoes"),
    path("cronogramas/<uuid:pk>/", views.detalhe_view, name="detalhe"),
    path("cronogramas/etapas/<uuid:pk>/alternar/", views.etapa_alternar_view, name="etapa_alternar"),
]