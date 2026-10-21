from django.conf import settings
from django.db import models

from core.models import ModeloBase


class Projeto(ModeloBase):
    nome = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    criador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="projetos_criados",
    )
    membros = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="MembroProjeto",
        related_name="projetos",
    )

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "projeto"
        verbose_name_plural = "projetos"

    def __str__(self):
        return self.nome


class MembroProjeto(ModeloBase):
    class Papel(models.TextChoices):
        ADMIN = "admin", "Admin"
        MEMBRO = "membro", "Membro"

    projeto = models.ForeignKey(
        Projeto,
        on_delete=models.CASCADE,
        related_name="vinculos",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vinculos_projetos",
    )
    papel = models.CharField(
        max_length=10,
        choices=Papel.choices,
        default=Papel.MEMBRO,
    )
    ultimo_acesso_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "membro do projeto"
        verbose_name_plural = "membros do projeto"
        constraints = [
            models.UniqueConstraint(
                fields=["projeto", "usuario"],
                name="unico_usuario_por_projeto",
            )
        ]
        indexes = [
            models.Index(fields=["usuario", "-ultimo_acesso_em"]),
        ]

    def __str__(self):
        return f"{self.usuario} em {self.projeto} ({self.get_papel_display()})"

    @property
    def eh_admin(self):
        return self.papel == self.Papel.ADMIN