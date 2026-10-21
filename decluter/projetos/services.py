from django.db import transaction
from django.utils import timezone

from .models import MembroProjeto, Projeto


class RegraDeProjetoError(Exception):
    """Levantada quando uma operação viola uma regra de negócio dos projetos."""


@transaction.atomic
def criar_projeto(*, nome, criador, descricao=""):
    projeto = Projeto.objects.create(
        nome=nome,
        descricao=descricao,
        criador=criador,
    )
    MembroProjeto.objects.create(
        projeto=projeto,
        usuario=criador,
        papel=MembroProjeto.Papel.ADMIN,
    )
    return projeto


def registrar_acesso(*, projeto, usuario):
    MembroProjeto.objects.filter(projeto=projeto, usuario=usuario).update(
        ultimo_acesso_em=timezone.now()
    )


@transaction.atomic
def alterar_papel(*, projeto, usuario, novo_papel):
    vinculos = list(
        MembroProjeto.objects.select_for_update().filter(projeto=projeto)
    )
    vinculo = next((v for v in vinculos if v.usuario_id == usuario.id), None)
    if vinculo is None:
        raise RegraDeProjetoError("Este usuário não é membro do projeto.")

    admins = [v for v in vinculos if v.papel == MembroProjeto.Papel.ADMIN]
    rebaixando_ultimo_admin = (
        vinculo.papel == MembroProjeto.Papel.ADMIN
        and novo_papel != MembroProjeto.Papel.ADMIN
        and len(admins) == 1
    )
    if rebaixando_ultimo_admin:
        raise RegraDeProjetoError("O projeto precisa ter pelo menos um Admin.")

    vinculo.papel = novo_papel
    vinculo.save(update_fields=["papel", "atualizado_em"])
    return vinculo