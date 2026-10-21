from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from boards.models import Board, Coluna

from .forms import ProjetoForm
from .models import MembroProjeto
from .services import criar_projeto


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
            return redirect("projetos:lista")
    else:
        form = ProjetoForm()

    return render(request, "projetos/criar.html", {"form": form})