from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.utils import timezone
from django.views.decorators.http import require_POST
from projetos.models import MembroProjeto
from .models import Board, Coluna, Tarefa


def _membro_ou_404(request, projeto_pk):
    # Só deixa passar quem participa do projeto
    return get_object_or_404(MembroProjeto, projeto__pk=projeto_pk, usuario=request.user)


@login_required
def detalhe_view(request, projeto_pk):
    membro = _membro_ou_404(request, projeto_pk)

    # Registra o acesso (alimenta "Projetos recentes" do dashboard)
    membro.ultimo_acesso = timezone.now()
    membro.save(update_fields=["ultimo_acesso"])

    board = get_object_or_404(Board, projeto=membro.projeto)
    colunas = board.colunas.prefetch_related(
        Prefetch("tarefas", queryset=Tarefa.objects.select_related("responsavel").order_by("prazo", "criado_em"))
    )

    return render(request, "boards/board.html", {
        "projeto": membro.projeto,
        "colunas": colunas,
        "tarefa_destaque": request.GET.get("tarefa"),
    })


@login_required
@require_POST
def tarefa_criar_view(request, projeto_pk):
    membro = _membro_ou_404(request, projeto_pk)
    coluna = get_object_or_404(Coluna, pk=request.POST.get("coluna"), board__projeto=membro.projeto)

    titulo = request.POST.get("titulo", "").strip()
    prioridade = request.POST.get("prioridade", "media")
    if prioridade not in dict(Tarefa.PRIORIDADE_CHOICES):
        prioridade = "media"

    if titulo:
        Tarefa.objects.create(
            coluna=coluna,
            titulo=titulo,
            responsavel=request.user,
            prioridade=prioridade,
            prazo=request.POST.get("prazo") or None,
        )
    return redirect("boards:detalhe", projeto_pk=projeto_pk)


@login_required
@require_POST
def tarefa_mover_view(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk, coluna__board__projeto__membros__usuario=request.user)
    coluna = get_object_or_404(Coluna, pk=request.POST.get("coluna"), board=tarefa.coluna.board)
    tarefa.coluna = coluna
    tarefa.save()
    return redirect("boards:detalhe", projeto_pk=coluna.board.projeto.pk)