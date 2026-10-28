from django.urls import path
from . import views

app_name = "projetos"

urlpatterns = [
    path("projetos/", views.lista_view, name="lista"),
    path("projetos/novo/", views.criar_view, name="criar"),
    path("projetos/<uuid:projeto_pk>/membros/", views.membros_view, name="membros"),
    path("projetos/<uuid:projeto_pk>/membros/adicionar/", views.membro_adicionar_view, name="membro_adicionar"),
    path("projetos/<uuid:projeto_pk>/membros/<uuid:usuario_pk>/papel/", views.membro_papel_view, name="membro_papel"),
    path("projetos/<uuid:projeto_pk>/membros/<uuid:usuario_pk>/remover/", views.membro_remover_view, name="membro_remover"),
]