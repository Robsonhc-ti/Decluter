from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from boards.models import Board, Coluna, Tarefa
from cronogramas.models import Cronograma, EtapaCronograma, SessaoEstudo
from projetos.models import MembroProjeto, Projeto


class DashboardTests(TestCase):
    def setUp(self):
        usuario_modelo = get_user_model()
        self.usuario = usuario_modelo.objects.create_user(
            username="dashboard-user",
            email="dashboard@example.com",
            password="senha-de-teste",
        )
        self.outro_usuario = usuario_modelo.objects.create_user(
            username="outro-dashboard-user",
            email="outro-dashboard@example.com",
            password="senha-de-teste",
        )
        self.client.force_login(self.usuario)

    def criar_cronograma(self, usuario, nome):
        cronograma = Cronograma.objects.create(
            usuario=usuario,
            nome=nome,
            tema="Tema de teste",
            tempo_por_dia="1h",
            nivel="iniciante",
            status=Cronograma.Status.PRONTO,
        )
        etapa = EtapaCronograma.objects.create(
            cronograma=cronograma,
            titulo=f"Etapa de {nome}",
            minutos_estimados=30,
        )
        sessao = SessaoEstudo.objects.create(
            etapa=etapa,
            data=timezone.localdate(),
            minutos=30,
        )
        return cronograma, etapa, sessao

    def criar_projeto_e_coluna(self, usuario, nome):
        projeto = Projeto.objects.create(
            nome=nome,
            descricao="",
            criador=usuario,
        )
        MembroProjeto.objects.create(
            projeto=projeto,
            usuario=usuario,
            papel=MembroProjeto.Papel.ADMIN,
        )
        board = Board.objects.create(projeto=projeto)
        coluna = Coluna.objects.create(
            board=board,
            nome="A fazer",
            concluida=False,
        )
        return projeto, coluna

    def criar_tarefa(self, coluna, responsavel, titulo, prazo=None):
        return Tarefa.objects.create(
            coluna=coluna,
            responsavel=responsavel,
            titulo=titulo,
            prazo=prazo,
        )

    def test_dashboard_mostra_apenas_dados_proprios_e_tarefas_de_projetos_com_vinculo(self):
        self.criar_cronograma(self.usuario, "Cronograma meu")
        self.criar_cronograma(self.outro_usuario, "Cronograma alheio")

        projeto, coluna = self.criar_projeto_e_coluna(
            self.usuario,
            "Projeto meu",
        )
        tarefa = self.criar_tarefa(
            coluna,
            self.usuario,
            "Tarefa minha",
            timezone.localdate(),
        )
        MembroProjeto.objects.create(
            projeto=projeto,
            usuario=self.outro_usuario,
            papel=MembroProjeto.Papel.MEMBRO,
        )
        self.criar_tarefa(
            coluna,
            self.outro_usuario,
            "Tarefa de outro membro",
        )

        projeto_alheio, coluna_alheia = self.criar_projeto_e_coluna(
            self.outro_usuario,
            "Projeto alheio",
        )
        tarefa_sem_vinculo = self.criar_tarefa(
            coluna_alheia,
            self.usuario,
            "Tarefa sem vínculo",
        )
        self.criar_tarefa(
            coluna,
            self.outro_usuario,
            "Tarefa de outra pessoa",
        )

        resposta = self.client.get(reverse("dashboard"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Etapa de Cronograma meu")
        self.assertContains(resposta, "Cronograma meu")
        self.assertContains(resposta, "Tarefa minha")
        self.assertContains(resposta, "Total: 30 minutos")
        self.assertContains(resposta, reverse("boards:tarefa_detalhe", args=[tarefa.pk]))
        self.assertContains(resposta, "Projeto meu")
        self.assertNotContains(resposta, "Cronograma alheio")
        self.assertNotContains(resposta, "Projeto alheio")
        self.assertNotContains(resposta, "Tarefa sem vínculo")
        self.assertNotContains(resposta, "Tarefa de outra pessoa")
        self.assertNotContains(resposta, "Tarefa de outro membro")
        self.assertNotContains(resposta, "atrasad")
        self.assertTrue(Projeto.objects.filter(pk=projeto.pk).exists())
        self.assertTrue(Projeto.objects.filter(pk=projeto_alheio.pk).exists())
        self.assertTrue(Tarefa.objects.filter(pk=tarefa_sem_vinculo.pk).exists())

    def test_dashboard_mostra_estado_vazio(self):
        resposta = self.client.get(reverse("dashboard"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Hoje está livre.")
        self.assertContains(resposta, "Total: 0 minutos")
        self.assertContains(resposta, "Nenhuma próxima tarefa.")
        self.assertContains(resposta, "Nenhum projeto ainda.")
        self.assertContains(resposta, "Nenhum cronograma em andamento.")

    def test_checkbox_da_sessao_retorna_ao_dashboard(self):
        _, _, sessao = self.criar_cronograma(self.usuario, "Cronograma de hoje")
        resposta = self.client.post(
            reverse("cronogramas:sessao_alternar", args=[sessao.pk]),
            {"next": reverse("dashboard")},
        )

        self.assertRedirects(resposta, reverse("dashboard"))
        sessao.refresh_from_db()
        self.assertTrue(sessao.concluida)

    def test_checkbox_rejeita_next_externo_e_volta_ao_dashboard(self):
        _, _, sessao = self.criar_cronograma(self.usuario, "Cronograma de hoje")

        resposta = self.client.post(
            reverse("cronogramas:sessao_alternar", args=[sessao.pk]),
            {"next": "https://example.com/"},
        )

        self.assertRedirects(resposta, reverse("dashboard"))

    def test_tarefas_sao_limitadas_a_oito_e_sem_prazo_fica_no_final(self):
        _, coluna = self.criar_projeto_e_coluna(self.usuario, "Projeto de tarefas")
        hoje = timezone.localdate()
        for indice in range(7):
            self.criar_tarefa(
                coluna,
                self.usuario,
                f"Tarefa com prazo {indice}",
                hoje + timedelta(days=indice),
            )
        self.criar_tarefa(coluna, self.usuario, "Tarefa sem prazo 1")
        self.criar_tarefa(coluna, self.usuario, "Tarefa sem prazo 2")

        resposta = self.client.get(reverse("dashboard"))
        tarefas = list(resposta.context["proximas_tarefas"])

        self.assertEqual(len(tarefas), 8)
        self.assertEqual(tarefas[-1].titulo, "Tarefa sem prazo 1")
        self.assertTrue(all(
            tarefas[indice].prazo <= tarefas[indice + 1].prazo
            for indice in range(6)
        ))

    def test_cronograma_exibe_percentual_das_sessoes_concluidas(self):
        cronograma, etapa, _ = self.criar_cronograma(
            self.usuario,
            "Cronograma parcial",
        )
        SessaoEstudo.objects.create(
            etapa=etapa,
            data=timezone.localdate(),
            minutos=30,
            concluida=True,
        )

        resposta = self.client.get(reverse("dashboard"))

        self.assertContains(resposta, "50% concluído")
        self.assertContains(resposta, "(1/2 sessões)")
        self.assertContains(
            resposta,
            reverse("cronogramas:detalhe", args=[cronograma.pk]),
        )

    def test_quantidade_de_consultas_nao_cresce_com_os_itens(self):
        _, coluna = self.criar_projeto_e_coluna(self.usuario, "Projeto de consultas")
        self.criar_tarefa(coluna, self.usuario, "Tarefa inicial")
        self.criar_cronograma(self.usuario, "Cronograma inicial")

        with CaptureQueriesContext(connection) as poucas_consultas:
            resposta = self.client.get(reverse("dashboard"))
        self.assertEqual(resposta.status_code, 200)
        quantidade_inicial = len(poucas_consultas)

        for indice in range(5):
            self.criar_tarefa(coluna, self.usuario, f"Tarefa extra {indice}")
            self.criar_cronograma(self.usuario, f"Cronograma extra {indice}")

        with CaptureQueriesContext(connection) as muitas_consultas:
            resposta = self.client.get(reverse("dashboard"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(muitas_consultas), quantidade_inicial)
