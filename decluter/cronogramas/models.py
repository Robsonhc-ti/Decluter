from django.db import models
from django.conf import settings
from django.utils import timezone
from core.models import ModeloBase


def _dias_uteis_padrao():
    return list(range(5))


class Cronograma(ModeloBase):
    class Tipo(models.TextChoices):
        TEMA = "tema", "Tema livre"
        FACULDADE = "faculdade", "Faculdade"
        ENEM = "enem", "ENEM"

    class Status(models.TextChoices):
        GERANDO = "gerando", "Gerando"
        PRONTO = "pronto", "Pronto"
        FALHOU = "falhou", "Falhou"

    NIVEL_CHOICES = [
        ("iniciante", "Iniciante"),
        ("intermediario", "Intermediário"),
        ("avancado", "Avançado"),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cronogramas")
    nome = models.CharField(max_length=200)
    tema = models.CharField(max_length=200)
    tempo_por_dia = models.CharField(max_length=50)
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES)
    complemento = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.TEMA)
    instituicao = models.CharField(max_length=200, blank=True)
    curso = models.CharField(max_length=200, blank=True)
    fontes = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.GERANDO,
    )
    erro = models.TextField(blank=True)
    data_inicio = models.DateField(default=timezone.localdate)
    dias_estudo = models.JSONField(default=_dias_uteis_padrao)

    def __str__(self):
        return self.nome


class EtapaCronograma(ModeloBase):
    cronograma = models.ForeignKey(Cronograma, on_delete=models.CASCADE, related_name="etapas")
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    concluida = models.BooleanField(default=False)
    ordem = models.PositiveIntegerField(default=0)
    recursos = models.JSONField(default=list, blank=True)
    minutos_estimados = models.PositiveIntegerField(default=60)

    class Meta:
        ordering = ["ordem"]

    def __str__(self):
        return self.titulo


class SessaoEstudo(ModeloBase):
    etapa = models.ForeignKey(
        EtapaCronograma,
        on_delete=models.CASCADE,
        related_name="sessoes",
    )
    data = models.DateField()
    minutos = models.PositiveIntegerField()
    concluida = models.BooleanField(default=False)

    class Meta:
        ordering = ["data", "etapa__ordem"]

    def __str__(self):
        return f"{self.etapa} — {self.data}"