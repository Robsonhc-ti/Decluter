from django.db.models import F
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from boards.models import Tarefa
from cronogramas.models import EtapaCronograma
from projetos.models import MembroProjeto


@login_required
def dashboard_view(request):
    hoje = timezone.now().date()

    # Tarefas do usuário que ainda não estão na coluna "Concluído"
    tarefas_usuario = Tarefa.objects.filter(
        responsavel=request.user
    ).exclude(coluna__concluida=True).select_related("coluna__board__projeto")

    tarefas_atrasadas = tarefas_usuario.filter(prazo__lt=hoje)
    proximos_eventos = tarefas_usuario.filter(prazo__gte=hoje).order_by("prazo")[:5]

    etapas_pendentes = EtapaCronograma.objects.filter(
        cronograma__usuario=request.user, concluida=False
    )

    projetos_recentes = MembroProjeto.objects.filter(
    usuario=request.user
).select_related("projeto").order_by(
    F("ultimo_acesso_em").desc(nulls_last=True)
)[:5]

    return render(request, "core/dashboard.html", {
        "qtd_pendentes": tarefas_usuario.count(),
        "qtd_cronogramas_pendentes": etapas_pendentes.count(),
        "qtd_atrasadas": tarefas_atrasadas.count(),
        "tarefas_pendentes": tarefas_usuario,
        "tarefas_atrasadas": tarefas_atrasadas,
        "projetos_recentes": projetos_recentes,
        "proximos_eventos": proximos_eventos,
    })