from django.contrib.auth import get_user_model
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


def _vinculos_travados(projeto, usuario):
    """Trava os vínculos do projeto e devolve (vinculo_do_usuario, lista_de_admins)."""
    vinculos = list(
        MembroProjeto.objects.select_for_update().filter(projeto=projeto)
    )
    vinculo = next((v for v in vinculos if v.usuario_id == usuario.id), None)
    if vinculo is None:
        raise RegraDeProjetoError("Este usuário não é membro do projeto.")
    admins = [v for v in vinculos if v.papel == MembroProjeto.Papel.ADMIN]
    return vinculo, admins


@transaction.atomic
def adicionar_membro(*, projeto, email):
    usuario = get_user_model().objects.filter(email__iexact=email.strip()).first()
    if usuario is None:
        raise RegraDeProjetoError("Nenhum usuário encontrado com esse e-mail.")

    vinculo, criado = MembroProjeto.objects.get_or_create(
        projeto=projeto,
        usuario=usuario,
        defaults={"papel": MembroProjeto.Papel.MEMBRO},
    )
    if not criado:
        raise RegraDeProjetoError("Este usuário já faz parte do projeto.")
    return vinculo


@transaction.atomic
def alterar_papel(*, projeto, usuario, novo_papel):
    vinculo, admins = _vinculos_travados(projeto, usuario)

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


@transaction.atomic
def remover_membro(*, projeto, usuario):
    from boards.models import Tarefa  # import local evita dependência circular entre apps

    vinculo, admins = _vinculos_travados(projeto, usuario)

    if vinculo.papel == MembroProjeto.Papel.ADMIN and len(admins) == 1:
        raise RegraDeProjetoError("O projeto precisa ter pelo menos um Admin.")

    Tarefa.objects.filter(
        coluna__board__projeto=projeto, responsavel=usuario
    ).update(responsavel=None)
    vinculo.delete()