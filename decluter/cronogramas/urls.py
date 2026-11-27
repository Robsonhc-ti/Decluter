from django.urls import path
from . import views

app_name = "cronogramas"

urlpatterns = [
    path("cronogramas/", views.lista_view, name="lista"),
    path("cronogramas/novo/", views.criar_view, name="criar"),
    path("cronogramas/<uuid:pk>/excluir/", views.excluir_view, name="excluir"),
    path("cronogramas/novo/faculdade/", views.criar_faculdade_view, name="criar_faculdade"),
    path("cronogramas/novo/enem/", views.criar_enem_view, name="criar_enem"),
    path("cronogramas/sugestoes/", views.sugestoes_view, name="sugestoes"),
    path("cronogramas/<uuid:pk>/status/", views.status_view, name="status"),
    path(
        "cronogramas/<uuid:pk>/tentar-novamente/",
        views.tentar_novamente_view,
        name="tentar_novamente",
    ),
    path("cronogramas/<uuid:pk>/", views.detalhe_view, name="detalhe"),
    path(
        "cronogramas/sessoes/<uuid:pk>/alternar/",
        views.sessao_alternar_view,
        name="sessao_alternar",
    ),
    path("cronogramas/etapas/<uuid:pk>/alternar/", views.etapa_alternar_view, name="etapa_alternar"),
]