from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from boards.models import Board, Coluna

from .forms import ProjetoForm
from .models import MembroProjeto
from .services import (
    RegraDeProjetoError,
    adicionar_membro,
    alterar_papel,
    criar_projeto,
    remover_membro,
)


def _vinculo_do_usuario(request, projeto_pk):
    return get_object_or_404(
        MembroProjeto.objects.select_related("projeto"),
        projeto_id=projeto_pk,
        usuario=request.user,
    )


def _exigir_admin(vinculo):
    if not vinculo.eh_admin:
        raise PermissionDenied("Apenas administradores podem fazer isso.")


@login_required
def lista_view(request):
    participacoes = (
        MembroProjeto.objects.filter(usuario=request.user)
        .select_related("projeto")
        .order_by("-projeto__criado_em")
    )
    return render(request, "projetos/lista.html", {"participacoes": participacoes})


@login_required
def criar_view(request):
    if request.method == "POST":
        form = ProjetoForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                projeto = criar_projeto(
                    nome=form.cleaned_data["nome"],
                    descricao=form.cleaned_data["descricao"],
                    criador=request.user,
                )
                board = Board.objects.create(projeto=projeto)
                colunas_padrao = [("A fazer", False), ("Fazendo", False), ("Concluído", True)]
                for ordem, (nome, concluida) in enumerate(colunas_padrao):
                    Coluna.objects.create(board=board, nome=nome, ordem=ordem, concluida=concluida)
            return redirect("boards:detalhe", projeto_pk=projeto.id)
    else:
        form = ProjetoForm()

    return render(request, "projetos/criar.html", {"form": form})


@login_required
def membros_view(request, projeto_pk):
    vinculo = _vinculo_do_usuario(request, projeto_pk)
    membros = (
        MembroProjeto.objects.filter(projeto=vinculo.projeto)
        .select_related("usuario")
        .order_by("papel", "usuario__username")
    )
    return render(request, "projetos/membros.html", {
        "projeto": vinculo.projeto,
        "membros": membros,
        "papeis": MembroProjeto.Papel.choices,
        "eh_admin": vinculo.eh_admin,
    })


@login_required
@require_POST
def membro_adicionar_view(request, projeto_pk):
    vinculo = _vinculo_do_usuario(request, projeto_pk)
    _exigir_admin(vinculo)

    try:
        novo = adicionar_membro(projeto=vinculo.projeto, email=request.POST.get("email", ""))
        messages.success(request, f"{novo.usuario.email} foi adicionado ao projeto.")
    except RegraDeProjetoError as erro:
        messages.error(request, str(erro))

    return redirect("projetos:membros", projeto_pk=projeto_pk)


@login_required
@require_POST
def membro_papel_view(request, projeto_pk, usuario_pk):
    vinculo = _vinculo_do_usuario(request, projeto_pk)
    _exigir_admin(vinculo)

    alvo = get_object_or_404(
        MembroProjeto.objects.select_related("usuario"),
        projeto_id=projeto_pk,
        usuario_id=usuario_pk,
    )
    novo_papel = request.POST.get("papel")
    if novo_papel not in MembroProjeto.Papel.values:
        messages.error(request, "Papel inválido.")
    else:
        try:
            alterar_papel(projeto=vinculo.projeto, usuario=alvo.usuario, novo_papel=novo_papel)
        except RegraDeProjetoError as erro:
            messages.error(request, str(erro))

    return redirect("projetos:membros", projeto_pk=projeto_pk)


@login_required
@require_POST
def membro_remover_view(request, projeto_pk, usuario_pk):
    vinculo = _vinculo_do_usuario(request, projeto_pk)
    saindo = vinculo.usuario_id == usuario_pk
    if not saindo:
        _exigir_admin(vinculo)

    alvo = get_object_or_404(
        MembroProjeto.objects.select_related("usuario"),
        projeto_id=projeto_pk,
        usuario_id=usuario_pk,
    )
    try:
        remover_membro(projeto=vinculo.projeto, usuario=alvo.usuario)
    except RegraDeProjetoError as erro:
        messages.error(request, str(erro))
        return redirect("projetos:membros", projeto_pk=projeto_pk)

    if saindo:
        return redirect("projetos:lista")
    return redirect("projetos:membros", projeto_pk=projeto_pk)