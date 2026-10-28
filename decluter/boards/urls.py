from django.urls import path
from . import views

app_name = "boards"

urlpatterns = [
    path("projetos/<uuid:projeto_pk>/", views.detalhe_view, name="detalhe"),
    path("projetos/<uuid:projeto_pk>/tarefas/nova/", views.tarefa_criar_view, name="tarefa_criar"),
    path("tarefas/<uuid:pk>/", views.tarefa_detalhe_view, name="tarefa_detalhe"),
    path("tarefas/<uuid:pk>/editar/", views.tarefa_editar_view, name="tarefa_editar"),
    path("tarefas/<uuid:pk>/excluir/", views.tarefa_excluir_view, name="tarefa_excluir"),
    path("tarefas/<uuid:pk>/mover/", views.tarefa_mover_view, name="tarefa_mover"),
    path("tarefas/<uuid:pk>/comentar/", views.comentario_criar_view, name="comentario_criar"),
]