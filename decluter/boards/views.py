from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Max, Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from projetos.models import MembroProjeto
from projetos.services import registrar_acesso

from .forms import TarefaForm
from .models import Board, Coluna, Comentario, Tarefa


def _buscar_coluna(board, coluna_id):
    try:
        return Coluna.objects.get(pk=coluna_id, board=board)
    except (Coluna.DoesNotExist, ValidationError, ValueError):
        raise Http404("Coluna não encontrada.")


def _proxima_ordem(coluna):
    maior = coluna.tarefas.aggregate(m=Max("ordem"))["m"]
    return 0 if maior is None else maior + 1


def _tarefa_do_membro(request, pk):
    """Devolve (tarefa, vinculo). Dá 404 se a tarefa não existe ou se o usuário não é membro."""
    tarefa = get_object_or_404(
        Tarefa.objects.select_related("coluna__board__projeto", "responsavel"),
        pk=pk,
    )
    vinculo = get_object_or_404(
        MembroProjeto,
        projeto_id=tarefa.coluna.board.projeto_id,
        usuario=request.user,
    )
    return tarefa, vinculo


@login_required
def detalhe_view(request, projeto_pk):
    vinculo = get_object_or_404(
        MembroProjeto.objects.select_related("projeto"),
        projeto_id=projeto_pk,
        usuario=request.user,
    )
    projeto = vinculo.projeto
    board = get_object_or_404(Board, projeto=projeto)

    colunas = board.colunas.prefetch_related(
        Prefetch("tarefas", queryset=Tarefa.objects.select_related("responsavel"))
    )
    membros = get_user_model().objects.filter(vinculos_projetos__projeto=projeto)

    registrar_acesso(projeto=projeto, usuario=request.user)

    return render(request, "boards/board.html", {
        "projeto": projeto,
        "board": board,
        "colunas": colunas,
        "membros": membros,
        "prioridades": Tarefa.Prioridade.choices,
        "eh_admin": vinculo.eh_admin,
    })


@login_required
@require_POST
def tarefa_criar_view(request, projeto_pk):
    get_object_or_404(MembroProjeto, projeto_id=projeto_pk, usuario=request.user)
    board = get_object_or_404(Board, projeto_id=projeto_pk)
    coluna = _buscar_coluna(board, request.POST.get("coluna_id"))

    form = TarefaForm(request.POST, projeto=board.projeto)
    if form.is_valid():
        tarefa = form.save(commit=False)
        tarefa.coluna = coluna
        tarefa.ordem = _proxima_ordem(coluna)
        tarefa.save()
    else:
        messages.error(request, "Não foi possível criar a tarefa. Verifique os campos.")

    return redirect("boards:detalhe", projeto_pk=projeto_pk)


@login_required
@require_POST
def tarefa_mover_view(request, pk):
    tarefa, _ = _tarefa_do_membro(request, pk)
    board = tarefa.coluna.board

    destino = _buscar_coluna(board, request.POST.get("coluna_id"))
    if destino.pk != tarefa.coluna_id:
        tarefa.coluna = destino
        tarefa.ordem = _proxima_ordem(destino)
        tarefa.save(update_fields=["coluna", "ordem", "atualizado_em"])

    return redirect("boards:detalhe", projeto_pk=board.projeto_id)


@login_required
def tarefa_detalhe_view(request, pk):
    tarefa, vinculo = _tarefa_do_membro(request, pk)
    return render(request, "boards/tarefa.html", {
        "tarefa": tarefa,
        "projeto": tarefa.coluna.board.projeto,
        "comentarios": tarefa.comentarios.select_related("usuario"),
        "eh_admin": vinculo.eh_admin,
    })


@login_required
def tarefa_editar_view(request, pk):
    tarefa, _ = _tarefa_do_membro(request, pk)
    projeto = tarefa.coluna.board.projeto

    if request.method == "POST":
        form = TarefaForm(request.POST, instance=tarefa, projeto=projeto)
        if form.is_valid():
            form.save()
            return redirect("boards:tarefa_detalhe", pk=tarefa.pk)
    else:
        form = TarefaForm(instance=tarefa, projeto=projeto)

    return render(request, "boards/tarefa_form.html", {
        "form": form,
        "tarefa": tarefa,
        "projeto": projeto,
    })


@login_required
@require_POST
def tarefa_excluir_view(request, pk):
    tarefa, vinculo = _tarefa_do_membro(request, pk)
    if not vinculo.eh_admin:
        raise PermissionDenied("Só administradores podem excluir tarefas.")

    projeto_id = tarefa.coluna.board.projeto_id
    tarefa.delete()
    return redirect("boards:detalhe", projeto_pk=projeto_id)


@login_required
@require_POST
def comentario_criar_view(request, pk):
    tarefa, _ = _tarefa_do_membro(request, pk)
    texto = request.POST.get("texto", "").strip()

    if texto:
        Comentario.objects.create(tarefa=tarefa, usuario=request.user, texto=texto)
    else:
        messages.error(request, "O comentário não pode ficar vazio.")

    return redirect("boards:tarefa_detalhe", pk=tarefa.pk)