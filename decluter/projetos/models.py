from django.conf import settings
from django.db import models
from core.models import ModeloBase


class Projeto(ModeloBase):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)

    def __str__(self):
        return self.nome


class ProjetoMembro(ModeloBase):
    PAPEL_CHOICES = [
        ("admin", "Administrador"),
        ("membro", "Membro"),
    ]

    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name="membros")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="participacoes")
    papel = models.CharField(max_length=20, choices=PAPEL_CHOICES, default="membro")
    ultimo_acesso = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("projeto", "usuario")

    def __str__(self):
        return f"{self.usuario} em {self.projeto} ({self.papel})"