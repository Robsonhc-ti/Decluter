from django.db import models
from django.conf import settings
from core.models import ModeloBase


class Cronograma(ModeloBase):
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

    def __str__(self):
        return self.nome


class EtapaCronograma(ModeloBase):
    cronograma = models.ForeignKey(Cronograma, on_delete=models.CASCADE, related_name="etapas")
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    concluida = models.BooleanField(default=False)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordem"]

    def __str__(self):
        return self.titulo