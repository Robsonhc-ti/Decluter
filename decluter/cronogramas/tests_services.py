from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Cronograma, EtapaCronograma, SessaoEstudo
from .planejamento import SemDiasDisponiveisError
from .services import (
    MENSAGEM_FALHA_GERACAO,
    MENSAGEM_SEM_DIAS,
    CronogramaIA,
    EtapaIA,
    GeracaoCronogramaError,
    RecursoIA,
    gerar_etapas_do_cronograma,
)


class GerarEtapasDoCronogramaTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username="aluno",
            email="aluno@example.com",
            password="senha-de-teste",
        )
        self.cronograma = Cronograma.objects.create(
            usuario=usuario,
            nome="Plano de teste",
            tema="Matemática",
            tempo_por_dia="1h",
            nivel="iniciante",
            data_inicio=date(2026, 11, 25),
            dias_estudo=[0, 1, 2, 3, 4],
        )

    def criar_etapa_ia(self, minutos):
        return EtapaIA(
            titulo=f"Etapa de {minutos} minutos",
            descricao="Descrição da etapa.",
            minutos_estimados=minutos,
            recursos=[
                RecursoIA(
                    titulo="Vídeo de estudo",
                    tipo="video",
                    busca="matemática básica",
                )
            ],
        )

    def gerar_com_plano(self, etapas):
        with (
            patch(
                "cronogramas.services._pesquisar_material",
                return_value=(
                    "Material pesquisado",
                    [{"titulo": "Fonte oficial", "url": "https://example.com/fonte"}],
                ),
            ),
            patch(
                "cronogramas.services._estruturar_cronograma",
                return_value=CronogramaIA(etapas=etapas),
            ),
        ):
            return gerar_etapas_do_cronograma(self.cronograma.pk)

    def test_sucesso_salva_status_fontes_etapas_e_sessoes(self):
        etapa_antiga = EtapaCronograma.objects.create(
            cronograma=self.cronograma,
            titulo="Etapa antiga",
            descricao="Será substituída.",
            minutos_estimados=30,
        )
        sessao_antiga = SessaoEstudo.objects.create(
            etapa=etapa_antiga,
            data=date(2026, 11, 25),
            minutos=30,
        )

        cronograma = self.gerar_com_plano([self.criar_etapa_ia(60)])

        cronograma.refresh_from_db()
        self.assertEqual(cronograma.status, Cronograma.Status.PRONTO)
        self.assertEqual(cronograma.erro, "")
        self.assertEqual(
            cronograma.fontes,
            [{"titulo": "Fonte oficial", "url": "https://example.com/fonte"}],
        )
        self.assertFalse(SessaoEstudo.objects.filter(pk=sessao_antiga.pk).exists())
        self.assertEqual(cronograma.etapas.count(), 1)
        self.assertGreater(cronograma.etapas.first().sessoes.count(), 0)
        recurso = cronograma.etapas.first().recursos[0]
        self.assertEqual(
            recurso["url"],
            "https://www.youtube.com/results?search_query=matem%C3%A1tica+b%C3%A1sica",
        )

    def test_falha_da_ia_salva_estado_e_mensagem_amigavel(self):
        with (
            patch(
                "cronogramas.services._pesquisar_material",
                return_value=("", []),
            ),
            patch(
                "cronogramas.services._estruturar_cronograma",
                side_effect=GeracaoCronogramaError(
                    "Chave da API do Gemini indisponível: segredo"
                ),
            ),
        ):
            cronograma = gerar_etapas_do_cronograma(self.cronograma.pk)

        cronograma.refresh_from_db()
        self.assertEqual(cronograma.status, Cronograma.Status.FALHOU)
        self.assertEqual(cronograma.erro, MENSAGEM_FALHA_GERACAO)
        self.assertNotIn("segredo", cronograma.erro)
        self.assertNotIn("API", cronograma.erro)

    def test_minutos_estimados_sao_limitados_entre_20_e_240(self):
        cronograma = self.gerar_com_plano([
            self.criar_etapa_ia(0),
            self.criar_etapa_ia(999),
        ])

        self.assertEqual(
            list(
                cronograma.etapas.order_by("ordem").values_list(
                    "minutos_estimados", flat=True
                )
            ),
            [20, 240],
        )

    def test_falha_no_agendamento_registra_mensagem_amigavel(self):
        with (
            patch(
                "cronogramas.services._pesquisar_material",
                return_value=("", []),
            ),
            patch(
                "cronogramas.services._estruturar_cronograma",
                return_value=CronogramaIA(
                    etapas=[self.criar_etapa_ia(60)]
                ),
            ),
            patch(
                "cronogramas.services.agendar_pendentes",
                side_effect=SemDiasDisponiveisError("detalhe técnico"),
            ),
        ):
            cronograma = gerar_etapas_do_cronograma(self.cronograma.pk)

        cronograma.refresh_from_db()
        self.assertEqual(cronograma.status, Cronograma.Status.FALHOU)
        self.assertEqual(cronograma.erro, MENSAGEM_SEM_DIAS)
        self.assertEqual(cronograma.etapas.count(), 0)
