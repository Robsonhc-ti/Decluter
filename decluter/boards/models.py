from django.conf import settings
from django.db import models

from core.models import ModeloBase
from projetos.models import Projeto


class Board(ModeloBase):
    projeto = models.OneToOneField(
        Projeto, on_delete=models.CASCADE, related_name="board"
    )

    def __str__(self):
        return f"Board de {self.projeto}"


class Coluna(ModeloBase):
    board = models.ForeignKey(
        Board, on_delete=models.CASCADE, related_name="colunas"
    )
    nome = models.CharField(max_length=100)
    ordem = models.PositiveIntegerField(default=0)
    concluida = models.BooleanField(default=False)

    class Meta:
        ordering = ["ordem"]

    def __str__(self):
        return self.nome


class Tarefa(ModeloBase):
    class Prioridade(models.TextChoices):
        BAIXA = "baixa", "Baixa"
        MEDIA = "media", "Média"
        ALTA = "alta", "Alta"
        URGENTE = "urgente", "Urgente"

    coluna = models.ForeignKey(
        Coluna, on_delete=models.CASCADE, related_name="tarefas"
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tarefas",
    )
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    prioridade = models.CharField(
        max_length=20, choices=Prioridade.choices, default=Prioridade.MEDIA
    )
    prazo = models.DateField(null=True, blank=True)
    ordem = models.PositiveIntegerField(default=0)
    campos_extras = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["ordem", "criado_em"]
        indexes = [
            models.Index(fields=["responsavel", "prazo"]),
        ]

    def __str__(self):
        return self.titulo


class Comentario(ModeloBase):
    tarefa = models.ForeignKey(
        Tarefa, on_delete=models.CASCADE, related_name="comentarios"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comentarios",
    )
    texto = models.TextField()

    class Meta:
        ordering = ["criado_em"]

    def __str__(self):
        return f"Comentário de {self.usuario} em {self.tarefa}"