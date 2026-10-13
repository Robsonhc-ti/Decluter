from django.urls import path
from . import views

app_name = "boards"

urlpatterns = [
    path("projetos/<uuid:projeto_pk>/", views.detalhe_view, name="detalhe"),
    path("projetos/<uuid:projeto_pk>/tarefas/nova/", views.tarefa_criar_view, name="tarefa_criar"),
    path("tarefas/<uuid:pk>/mover/", views.tarefa_mover_view, name="tarefa_mover"),
]