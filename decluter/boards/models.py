from django.conf import settings
from django.db import models
from core.models import ModeloBase
from projetos.models import Projeto


class Board(ModeloBase):
    projeto = models.OneToOneField(Projeto, on_delete=models.CASCADE, related_name="board")

    def __str__(self):
        return f"Board de {self.projeto}"


class Coluna(ModeloBase):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="colunas")
    nome = models.CharField(max_length=100)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordem"]

    def __str__(self):
        return self.nome


class Tarefa(ModeloBase):
    PRIORIDADE_CHOICES = [
        ("baixa", "Baixa"),
        ("media", "Média"),
        ("alta", "Alta"),
        ("urgente", "Urgente"),
    ]

    coluna = models.ForeignKey(Coluna, on_delete=models.CASCADE, related_name="tarefas")
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="tarefas"
    )
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default="media")
    prazo = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.titulo


class Comentario(ModeloBase):
    tarefa = models.ForeignKey(Tarefa, on_delete=models.CASCADE, related_name="comentarios")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comentarios")
    texto = models.TextField()

    def __str__(self):
        return f"Comentário de {self.usuario} em {self.tarefa}"