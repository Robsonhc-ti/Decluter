from datetime import date, timedelta
from unittest import TestCase

from .planejamento import (
    JANELA_REPOSICAO,
    dividir,
    dias_de_estudo,
    interpretar_minutos,
    planejar_etapas,
    planejar_reposicao,
)

SEG = date(2026, 11, 2)   # segunda-feira
UTEIS = (0, 1, 2, 3, 4)


class InterpretarMinutosTests(TestCase):
    def test_formatos_comuns(self):
        casos = {
            "1h": 60, "2 horas": 120, "1h30": 90, "1h 30min": 90,
            "45 min": 45, "1.5h": 90, "1,5 h": 90, "45": 45, "2": 120,
            "1 hora e 30 minutos": 90, "": 60, "abc": 60,
        }
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(interpretar_minutos(texto), esperado)

    def test_limites(self):
        self.assertEqual(interpretar_minutos("5 min"), 30)
        self.assertEqual(interpretar_minutos("20h"), 720)


class DividirTests(TestCase):
    def test_divisao(self):
        self.assertEqual(dividir(40), [15, 15, 10])
        self.assertEqual(dividir(32), [15, 17])   # sobra de 2 min é somada
        self.assertEqual(dividir(10), [10])
        self.assertEqual(dividir(3), [3])
        self.assertEqual(sum(dividir(97)), 97)


class DiasDeEstudoTests(TestCase):
    def test_pula_fim_de_semana(self):
        dias = list(zip(range(6), dias_de_estudo(UTEIS, date(2026, 11, 6))))
        datas = [d for _, d in dias]
        self.assertEqual(datas[0].weekday(), 4)            # sexta
        self.assertEqual(datas[1], date(2026, 11, 9))      # segunda
        self.assertTrue(all(d.weekday() < 5 for d in datas))

    def test_sem_dias_escolhidos_usa_dias_uteis(self):
        primeiro = next(dias_de_estudo((), date(2026, 11, 7)))  # sábado
        self.assertEqual(primeiro, date(2026, 11, 9))


class PlanejarEtapasTests(TestCase):
    def test_sequencia_e_folga(self):
        # capacidade 60 -> meta de 45 min por dia
        sessoes = planejar_etapas([(1, 100), (2, 50)], inicio=SEG,
                                  dias_semana=UTEIS, capacidade=60)
        self.assertEqual(sessoes, [
            (1, SEG, 45),
            (1, SEG + timedelta(days=1), 45),
            (1, SEG + timedelta(days=2), 10),
            (2, SEG + timedelta(days=2), 35),
            (2, SEG + timedelta(days=3), 15),
        ])

    def test_conserva_total_e_respeita_meta(self):
        etapas = [(i, m) for i, m in enumerate([30, 90, 55, 120, 20])]
        sessoes = planejar_etapas(etapas, inicio=SEG, dias_semana=(0, 2, 4), capacidade=90)
        por_etapa, por_dia = {}, {}
        for etapa, dia, minutos in sessoes:
            por_etapa[etapa] = por_etapa.get(etapa, 0) + minutos
            por_dia[dia] = por_dia.get(dia, 0) + minutos
        self.assertEqual(por_etapa, dict(etapas))
        self.assertTrue(all(m <= 67 for m in por_dia.values()))   # 75% de 90
        self.assertTrue(all(d.weekday() in (0, 2, 4) for d in por_dia))

    def test_pula_fim_de_semana(self):
        sexta = date(2026, 11, 6)
        sessoes = planejar_etapas([(1, 100)], inicio=sexta, dias_semana=UTEIS, capacidade=60)
        self.assertEqual([d for _, d, _ in sessoes],
                         [sexta, date(2026, 11, 9), date(2026, 11, 10)])

    def test_respeita_carga_existente(self):
        sessoes = planejar_etapas([(1, 30)], inicio=SEG, dias_semana=UTEIS,
                                  capacidade=60, carga={SEG: 40})
        # segunda tem só 5 min livres (< 10): vai tudo para terça
        self.assertEqual(sessoes, [(1, SEG + timedelta(days=1), 30)])


def _carga_cheia(inicio, dias, minutos):
    carga = {}
    for dia in list(zip(range(dias), dias_de_estudo(UTEIS, inicio))):
        carga[dia[1]] = minutos
    return carga


class PlanejarReposicaoTests(TestCase):
    def test_reparte_em_pedacos_menores(self):
        hoje = date(2026, 11, 4)  # quarta
        carga = _carga_cheia(hoje, 14, 45)   # dias com 15 min livres (capacidade 60)
        agenda = planejar_reposicao([(1, 40)], hoje=hoje, dias_semana=UTEIS,
                                    capacidade=60, carga=carga)
        self.assertEqual(sum(agenda.values()), 40)
        self.assertEqual(agenda, {
            (1, date(2026, 11, 4)): 15,
            (1, date(2026, 11, 5)): 15,
            (1, date(2026, 11, 6)): 10,
        })

    def test_escolhe_o_dia_mais_livre(self):
        hoje = date(2026, 11, 4)
        quinta = date(2026, 11, 5)
        carga = _carga_cheia(hoje, 14, 50)
        carga[quinta] = 10   # dia bem mais vazio
        agenda = planejar_reposicao([(1, 15)], hoje=hoje, dias_semana=UTEIS,
                                    capacidade=60, carga=carga)
        self.assertEqual(agenda, {(1, quinta): 15})

    def test_nunca_passa_da_capacidade(self):
        hoje = date(2026, 11, 4)
        carga = _carga_cheia(hoje, 14, 45)
        agenda = planejar_reposicao([(1, 200), (2, 90)], hoje=hoje, dias_semana=UTEIS,
                                    capacidade=60, carga=carga)
        novo = {}
        for (_, dia), minutos in agenda.items():
            novo[dia] = novo.get(dia, 0) + minutos
        for dia, minutos in novo.items():
            self.assertLessEqual(carga.get(dia, 0) + minutos, 60)
        self.assertEqual(sum(agenda.values()), 290)

    def test_estende_alem_da_janela_quando_tudo_esta_cheio(self):
        hoje = date(2026, 11, 4)
        carga = _carga_cheia(hoje, JANELA_REPOSICAO, 60)   # janela toda lotada
        agenda = planejar_reposicao([(1, 15)], hoje=hoje, dias_semana=UTEIS,
                                    capacidade=60, carga=carga)
        (_, dia), = agenda.keys()
        self.assertNotIn(dia, carga)
        self.assertGreater(dia, max(carga))

    def test_sem_atrasos_nao_faz_nada(self):
        self.assertEqual(
            planejar_reposicao([], hoje=SEG, dias_semana=UTEIS, capacidade=60), {})

    def test_junta_pedacos_da_mesma_etapa_no_mesmo_dia(self):
        # dia com 45 min livres recebe os 3 pedaços da mesma etapa numa única sessão
        hoje = date(2026, 11, 4)
        carga = _carga_cheia(hoje, 14, 55)
        carga[hoje] = 0
        agenda = planejar_reposicao([(1, 45)], hoje=hoje, dias_semana=UTEIS,
                                    capacidade=60, carga=carga)
        self.assertEqual(agenda, {(1, hoje): 45})