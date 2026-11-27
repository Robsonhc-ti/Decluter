from collections import defaultdict
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .agenda import agendar_pendentes, replanejar_atrasos, sincronizar_etapa
from .models import Cronograma, EtapaCronograma, SessaoEstudo
from .planejamento import dias_de_estudo


class AgendaBancoTests(TestCase):
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
            data_inicio=date(2026, 11, 2),
            dias_estudo=[0, 1, 2, 3, 4],
        )

    def criar_etapa(self, *, ordem=0, minutos=60, concluida=False):
        return EtapaCronograma.objects.create(
            cronograma=self.cronograma,
            titulo=f"Etapa {ordem + 1}",
            ordem=ordem,
            minutos_estimados=minutos,
            concluida=concluida,
        )

    def test_agendar_pendentes_cria_sessoes(self):
        etapa_um = self.criar_etapa(ordem=0, minutos=60)
        etapa_dois = self.criar_etapa(ordem=1, minutos=30)

        criadas = agendar_pendentes(self.cronograma)

        self.assertEqual(len(criadas), 3)
        self.assertEqual(
            sum(s.minutos for s in etapa_um.sessoes.all()),
            etapa_um.minutos_estimados,
        )
        self.assertEqual(
            sum(s.minutos for s in etapa_dois.sessoes.all()),
            etapa_dois.minutos_estimados,
        )
        self.assertTrue(
            all(s.data.weekday() in self.cronograma.dias_estudo for s in criadas)
        )

    def test_agendar_pendentes_duas_chamadas_nao_duplicam_sessoes(self):
        self.criar_etapa(minutos=30)

        agendar_pendentes(self.cronograma)
        agendar_pendentes(self.cronograma)

        self.assertEqual(SessaoEstudo.objects.count(), 1)

    def test_agendar_pendentes_nao_cria_sessoes_no_passado(self):
        self.cronograma.data_inicio = date(2020, 1, 1)
        self.cronograma.save(update_fields=["data_inicio"])
        self.criar_etapa(minutos=30)

        agendar_pendentes(self.cronograma)

        hoje = timezone.localdate()
        self.assertTrue(
            all(
                sessao.data >= hoje
                for sessao in SessaoEstudo.objects.filter(
                    etapa__cronograma=self.cronograma
                )
            )
        )

    def test_replaneja_sessoes_antigas_sem_exceder_capacidade_ou_duplicar(self):
        etapa_atrasada = self.criar_etapa(ordem=0, minutos=30)
        etapa_carga = self.criar_etapa(ordem=1, minutos=60)
        hoje = date(2026, 11, 4)

        SessaoEstudo.objects.create(
            etapa=etapa_atrasada,
            data=date(2026, 11, 2),
            minutos=5,
        )
        SessaoEstudo.objects.create(
            etapa=etapa_atrasada,
            data=date(2026, 11, 3),
            minutos=10,
        )
        SessaoEstudo.objects.create(
            etapa=etapa_atrasada,
            data=hoje,
            minutos=45,
        )

        dias_futuros = list(dias_de_estudo(self.cronograma.dias_estudo, hoje))[:14]
        for dia in dias_futuros:
            if dia != hoje:
                SessaoEstudo.objects.create(
                    etapa=etapa_carga,
                    data=dia,
                    minutos=50,
                )

        replanejar_atrasos(self.cronograma, hoje=hoje)

        self.assertFalse(
            SessaoEstudo.objects.filter(
                etapa=etapa_atrasada,
                data__lt=hoje,
                concluida=False,
            ).exists()
        )
        sessoes_da_etapa_no_dia = SessaoEstudo.objects.filter(
            etapa=etapa_atrasada,
            data=hoje,
        )
        self.assertEqual(sessoes_da_etapa_no_dia.count(), 1)
        self.assertEqual(sessoes_da_etapa_no_dia.get().minutos, 60)

        carga_por_dia = defaultdict(int)
        for sessao in SessaoEstudo.objects.filter(
            etapa__cronograma=self.cronograma,
            data__gte=hoje,
        ):
            carga_por_dia[sessao.data] += sessao.minutos
        self.assertTrue(all(minutos <= 60 for minutos in carga_por_dia.values()))

    def test_reposicao_nao_soma_em_sessao_futura_concluida(self):
        etapa_atrasada = self.criar_etapa(ordem=0, minutos=30, concluida=True)
        etapa_carga = self.criar_etapa(ordem=1, minutos=60)
        hoje = date(2026, 11, 4)

        SessaoEstudo.objects.create(
            etapa=etapa_atrasada,
            data=date(2026, 11, 3),
            minutos=15,
        )
        concluida = SessaoEstudo.objects.create(
            etapa=etapa_atrasada,
            data=hoje,
            minutos=45,
            concluida=True,
        )

        dias_futuros = list(dias_de_estudo(self.cronograma.dias_estudo, hoje))[:14]
        for dia in dias_futuros:
            if dia != hoje:
                SessaoEstudo.objects.create(
                    etapa=etapa_carga,
                    data=dia,
                    minutos=50,
                )

        replanejar_atrasos(self.cronograma, hoje=hoje)

        concluida.refresh_from_db()
        self.assertEqual(concluida.minutos, 45)
        self.assertTrue(concluida.concluida)
        self.assertEqual(
            SessaoEstudo.objects.filter(
                etapa=etapa_atrasada,
                data=hoje,
                concluida=False,
                minutos=15,
            ).count(),
            1,
        )
        etapa_atrasada.refresh_from_db()
        self.assertFalse(etapa_atrasada.concluida)

    def test_sincronizar_etapa_conclui_reabre_e_nao_conclui_sem_sessoes(self):
        etapa = self.criar_etapa(concluida=True)
        self.assertFalse(sincronizar_etapa(etapa))

        primeira = SessaoEstudo.objects.create(
            etapa=etapa,
            data=date(2026, 11, 2),
            minutos=30,
            concluida=True,
        )
        segunda = SessaoEstudo.objects.create(
            etapa=etapa,
            data=date(2026, 11, 3),
            minutos=30,
            concluida=False,
        )

        self.assertFalse(sincronizar_etapa(etapa))
        segunda.concluida = True
        segunda.save(update_fields=["concluida"])
        self.assertTrue(sincronizar_etapa(etapa))

        primeira.concluida = False
        primeira.save(update_fields=["concluida"])
        self.assertFalse(sincronizar_etapa(etapa))
