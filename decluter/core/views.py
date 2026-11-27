from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Q
from django.shortcuts import render
from django.utils import timezone

from boards.models import Tarefa
from cronogramas.models import Cronograma, SessaoEstudo
from projetos.models import MembroProjeto


@login_required
def dashboard_view(request):
    usuario = request.user
    hoje = timezone.localdate()

    sessoes_hoje = list(
        SessaoEstudo.objects.filter(
            etapa__cronograma__usuario=usuario,
            data=hoje,
        )
        .select_related("etapa__cronograma")
        .order_by("etapa__cronograma__nome", "etapa__ordem")
    )
    total_minutos_hoje = sum(sessao.minutos for sessao in sessoes_hoje)

    tarefas_atribuidas_ao_usuario = Tarefa.objects.filter(
        responsavel=usuario,
    )
    proximas_tarefas = (
        tarefas_atribuidas_ao_usuario.filter(
            coluna__concluida=False,
            coluna__board__projeto__vinculos__usuario=usuario,
        )
        .select_related("coluna__board__projeto")
        .order_by(F("prazo").asc(nulls_last=True), "criado_em")[:8]
    )

    projetos_recentes = (
        MembroProjeto.objects.filter(usuario=usuario)
        .select_related("projeto")
        .order_by(F("ultimo_acesso_em").desc(nulls_last=True))[:5]
    )

    cronogramas_em_andamento = list(
        Cronograma.objects.filter(
            usuario=usuario,
            status=Cronograma.Status.PRONTO,
        )
        .annotate(
            total_sessoes=Count("etapas__sessoes", distinct=True),
            sessoes_concluidas=Count(
                "etapas__sessoes",
                filter=Q(etapas__sessoes__concluida=True),
                distinct=True,
            ),
        )
        .filter(total_sessoes__gt=F("sessoes_concluidas"))
        .order_by("-criado_em")[:5]
    )
    for cronograma in cronogramas_em_andamento:
        cronograma.percentual_concluido = int(
            cronograma.sessoes_concluidas * 100 / cronograma.total_sessoes
        )

    return render(request, "core/dashboard.html", {
        "hoje": hoje,
        "sessoes_hoje": sessoes_hoje,
        "total_minutos_hoje": total_minutos_hoje,
        "proximas_tarefas": proximas_tarefas,
        "projetos_recentes": projetos_recentes,
        "cronogramas_em_andamento": cronogramas_em_andamento,
    })
