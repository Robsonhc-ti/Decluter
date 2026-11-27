import os
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from boards.models import Board, Coluna, Tarefa
from cronogramas.agenda import sincronizar_etapa
from cronogramas.models import Cronograma, EtapaCronograma, SessaoEstudo
from projetos.models import MembroProjeto, Projeto


class Command(BaseCommand):
    help = "Cria dados de demonstração para a apresentação."

    def handle(self, *args, **options):
        senha = os.environ.get("DEMO_PASSWORD", "")
        if not senha:
            raise CommandError("Defina DEMO_PASSWORD no ambiente antes de executar.")

        with transaction.atomic():
            aluno = self._obter_usuario(
                email="demo.aluno@example.invalid",
                username="demo_aluno",
                nome="Aluno",
                senha=senha,
            )
            colega = self._obter_usuario(
                email="demo.colega@example.invalid",
                username="demo_colega",
                nome="Colega",
                senha=senha,
            )
            projeto = self._obter_projeto(aluno, colega)
            board = Board.objects.get_or_create(projeto=projeto)[0]
            colunas = self._obter_colunas(board)
            self._obter_tarefas(colunas, aluno, colega)
            self._obter_cronograma(aluno)

        self.stdout.write(self.style.SUCCESS(
            "Dados de demonstração preparados: demo_aluno e demo_colega."
        ))

    @staticmethod
    def _obter_usuario(email, username, nome, senha):
        usuario_modelo = get_user_model()
        usuario, _ = usuario_modelo.objects.get_or_create(
            email=email,
            defaults={
                "username": username,
                "first_name": nome,
            },
        )
        usuario.username = username
        usuario.first_name = nome
        usuario.is_active = True
        usuario.set_password(senha)
        usuario.save()
        return usuario

    @staticmethod
    def _obter_projeto(aluno, colega):
        projeto, _ = Projeto.objects.get_or_create(
            criador=aluno,
            nome="Projeto de demonstração",
            defaults={"descricao": "Organização de um trabalho escolar em equipe."},
        )
        projeto.descricao = "Organização de um trabalho escolar em equipe."
        projeto.save(update_fields=["descricao", "atualizado_em"])
        MembroProjeto.objects.update_or_create(
            projeto=projeto,
            usuario=aluno,
            defaults={"papel": MembroProjeto.Papel.ADMIN},
        )
        MembroProjeto.objects.update_or_create(
            projeto=projeto,
            usuario=colega,
            defaults={"papel": MembroProjeto.Papel.MEMBRO},
        )
        return projeto

    @staticmethod
    def _obter_colunas(board):
        configuracoes = [
            ("A fazer", 0, False),
            ("Em andamento", 1, False),
            ("Concluído", 2, True),
        ]
        colunas = {}
        for nome, ordem, concluida in configuracoes:
            coluna, _ = Coluna.objects.update_or_create(
                board=board,
                nome=nome,
                defaults={"ordem": ordem, "concluida": concluida},
            )
            colunas[nome] = coluna
        return colunas

    @staticmethod
    def _obter_tarefas(colunas, aluno, colega):
        hoje = timezone.localdate()
        tarefas = [
            (
                "A fazer",
                "Pesquisar fontes confiáveis",
                aluno,
                hoje + timedelta(days=2),
                Tarefa.Prioridade.ALTA,
            ),
            (
                "Em andamento",
                "Organizar o roteiro da apresentação",
                colega,
                hoje + timedelta(days=4),
                Tarefa.Prioridade.MEDIA,
            ),
            (
                "Concluído",
                "Escolher o tema do trabalho",
                aluno,
                hoje + timedelta(days=1),
                Tarefa.Prioridade.BAIXA,
            ),
        ]
        for nome_coluna, titulo, responsavel, prazo, prioridade in tarefas:
            Tarefa.objects.update_or_create(
                coluna=colunas[nome_coluna],
                titulo=titulo,
                defaults={
                    "responsavel": responsavel,
                    "prazo": prazo,
                    "prioridade": prioridade,
                },
            )

    @staticmethod
    def _obter_cronograma(aluno):
        hoje = timezone.localdate()
        cronograma, _ = Cronograma.objects.get_or_create(
            usuario=aluno,
            nome="Cronograma de demonstração",
            defaults={
                "tema": "Ciências: energia renovável",
                "tempo_por_dia": "1h",
                "nivel": "iniciante",
            },
        )
        cronograma.tema = "Ciências: energia renovável"
        cronograma.tempo_por_dia = "1h"
        cronograma.nivel = "iniciante"
        cronograma.status = Cronograma.Status.PRONTO
        cronograma.erro = ""
        cronograma.data_inicio = hoje
        cronograma.dias_estudo = list(range(7))
        cronograma.save()

        etapas = [
            ("Conceitos de energia renovável", "Revisar as principais fontes.", 30),
            ("Energia solar e eólica", "Comparar funcionamento e aplicações.", 45),
            ("Revisão do conteúdo", "Consolidar os pontos principais.", 30),
        ]
        for ordem, (titulo, descricao, minutos) in enumerate(etapas):
            etapa, _ = EtapaCronograma.objects.get_or_create(
                cronograma=cronograma,
                titulo=titulo,
                defaults={
                    "descricao": descricao,
                    "ordem": ordem,
                    "minutos_estimados": minutos,
                },
            )
            etapa.descricao = descricao
            etapa.ordem = ordem
            etapa.minutos_estimados = minutos
            etapa.save(update_fields=[
                "descricao",
                "ordem",
                "minutos_estimados",
                "atualizado_em",
            ])

            data_sessao = hoje + timedelta(days=ordem)
            sessao = etapa.sessoes.order_by("data", "pk").first()
            if sessao is None:
                sessao = SessaoEstudo(etapa=etapa)
            sessao.data = data_sessao
            sessao.minutos = minutos
            sessao.concluida = ordem == 0
            sessao.save()
            etapa.sessoes.exclude(pk=sessao.pk).delete()
            sincronizar_etapa(etapa)
