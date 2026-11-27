from datetime import date, timedelta

from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from .forms import CronogramaForm, EnemForm, FaculdadeForm
from .models import Cronograma, EtapaCronograma, SessaoEstudo
from .services import MENSAGEM_FALHA_GERACAO


class CronogramaViewsTests(TestCase):
    def setUp(self):
        usuario_modelo = get_user_model()
        self.dono = usuario_modelo.objects.create_user(
            username="dono",
            email="dono@example.com",
            password="senha-de-teste",
        )
        self.outro_usuario = usuario_modelo.objects.create_user(
            username="outro",
            email="outro@example.com",
            password="senha-de-teste",
        )
        self.cronograma = self.criar_cronograma(self.dono)
        self.client.force_login(self.dono)

    def criar_cronograma(self, usuario, **campos):
        valores = {
            "usuario": usuario,
            "nome": "Plano de teste",
            "tema": "Matemática",
            "tempo_por_dia": "1h",
            "nivel": "iniciante",
            "status": Cronograma.Status.PRONTO,
        }
        valores.update(campos)
        return Cronograma.objects.create(**valores)

    def test_formularios_aceitam_dias_como_inteiros_e_exigem_ao_menos_um(self):
        formularios = [CronogramaForm, FaculdadeForm, EnemForm]
        for formulario in formularios:
            campo = formulario.base_fields["dias_estudo"]
            self.assertIsInstance(campo, forms.MultipleChoiceField)
            self.assertIsInstance(campo.widget, forms.CheckboxSelectMultiple)
            self.assertEqual(campo.initial, [0, 1, 2, 3, 4])
            self.assertTrue(campo.required)
            self.assertEqual([valor for valor, _ in campo.choices], list(range(7)))

        form = CronogramaForm(data={
            "nome": "Plano",
            "tema": "Matemática",
            "tempo_por_dia": "1h",
            "nivel": "iniciante",
            "dias_estudo": ["1", "6"],
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["dias_estudo"], [1, 6])

        form_sem_dias = CronogramaForm(data={
            "nome": "Plano",
            "tema": "Matemática",
            "tempo_por_dia": "1h",
            "nivel": "iniciante",
            "dias_estudo": [],
        })
        self.assertFalse(form_sem_dias.is_valid())

    def test_criacao_enfileira_apos_commit_e_salva_dias_inteiros(self):
        dados = {
            "nome": "Novo plano",
            "tema": "Física",
            "tempo_por_dia": "1h",
            "nivel": "iniciante",
            "dias_estudo": ["0", "3"],
        }
        with (
            patch("cronogramas.views.gerar_cronograma_task.delay") as enfileirar,
            self.captureOnCommitCallbacks(execute=True),
        ):
            resposta = self.client.post(reverse("cronogramas:criar"), data=dados)

        cronograma = Cronograma.objects.get(nome="Novo plano")
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(cronograma.status, Cronograma.Status.GERANDO)
        self.assertEqual(cronograma.dias_estudo, [0, 3])
        enfileirar.assert_called_once_with(str(cronograma.pk))

    def test_falha_ao_enfileirar_marca_cronograma_com_erro_amigavel(self):
        with (
            patch(
                "cronogramas.views.gerar_cronograma_task.delay",
                side_effect=RuntimeError("detalhe interno"),
            ),
            self.captureOnCommitCallbacks(execute=True),
        ):
            resposta = self.client.post(
                reverse("cronogramas:criar"),
                data={
                    "nome": "Plano sem fila",
                    "tema": "Física",
                    "tempo_por_dia": "1h",
                    "nivel": "iniciante",
                    "dias_estudo": ["0"],
                },
            )

        cronograma = Cronograma.objects.get(nome="Plano sem fila")
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(cronograma.status, Cronograma.Status.FALHOU)
        self.assertEqual(cronograma.erro, MENSAGEM_FALHA_GERACAO)
        self.assertNotIn("detalhe interno", cronograma.erro)

    def test_status_view_retorna_json_e_nao_expoe_plano_de_outro_usuario(self):
        url = reverse("cronogramas:status", args=[self.cronograma.pk])
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.json(),
            {"status": Cronograma.Status.PRONTO, "erro": ""},
        )

        self.client.force_login(self.outro_usuario)
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 404)

    def test_status_view_exibe_geracao_travada_como_falha(self):
        Cronograma.objects.filter(pk=self.cronograma.pk).update(
            status=Cronograma.Status.GERANDO,
            atualizado_em=timezone.now() - timedelta(minutes=6),
        )

        resposta = self.client.get(
            reverse("cronogramas:status", args=[self.cronograma.pk])
        )

        self.assertEqual(resposta.json()["status"], Cronograma.Status.FALHOU)
        self.assertTrue(resposta.json()["erro"])

    def test_tentar_novamente_enfileira_somente_quando_falhou(self):
        url = reverse("cronogramas:tentar_novamente", args=[self.cronograma.pk])
        with (
            patch("cronogramas.views.gerar_cronograma_task.delay") as enfileirar,
            self.captureOnCommitCallbacks(execute=True),
        ):
            resposta = self.client.post(url)

        self.assertEqual(resposta.status_code, 302)
        enfileirar.assert_not_called()
        self.cronograma.refresh_from_db()
        self.assertEqual(self.cronograma.status, Cronograma.Status.PRONTO)

        self.cronograma.status = Cronograma.Status.FALHOU
        self.cronograma.erro = "Erro anterior."
        self.cronograma.save(update_fields=["status", "erro", "atualizado_em"])
        with (
            patch("cronogramas.views.gerar_cronograma_task.delay") as enfileirar,
            self.captureOnCommitCallbacks(execute=True),
        ):
            resposta = self.client.post(url)

        self.assertEqual(resposta.status_code, 302)
        self.cronograma.refresh_from_db()
        self.assertEqual(self.cronograma.status, Cronograma.Status.GERANDO)
        self.assertEqual(self.cronograma.erro, "")
        enfileirar.assert_called_once_with(str(self.cronograma.pk))

    def test_tentar_novamente_aceita_cronograma_travado(self):
        Cronograma.objects.filter(pk=self.cronograma.pk).update(
            status=Cronograma.Status.GERANDO,
            atualizado_em=timezone.now() - timedelta(minutes=6),
        )
        with (
            patch("cronogramas.views.gerar_cronograma_task.delay") as enfileirar,
            self.captureOnCommitCallbacks(execute=True),
        ):
            resposta = self.client.post(
                reverse("cronogramas:tentar_novamente", args=[self.cronograma.pk])
            )

        self.assertEqual(resposta.status_code, 302)
        self.cronograma.refresh_from_db()
        self.assertEqual(self.cronograma.status, Cronograma.Status.GERANDO)
        enfileirar.assert_called_once_with(str(self.cronograma.pk))

    def test_acoes_alteram_sessoes_e_exigem_post(self):
        etapa = EtapaCronograma.objects.create(
            cronograma=self.cronograma,
            titulo="Etapa 1",
            minutos_estimados=60,
        )
        sessao_um = SessaoEstudo.objects.create(
            etapa=etapa,
            data=date(2026, 11, 25),
            minutos=30,
        )
        sessao_dois = SessaoEstudo.objects.create(
            etapa=etapa,
            data=date(2026, 11, 26),
            minutos=30,
        )

        url_sessao = reverse("cronogramas:sessao_alternar", args=[sessao_um.pk])
        url_etapa = reverse("cronogramas:etapa_alternar", args=[etapa.pk])
        self.assertEqual(self.client.get(url_sessao).status_code, 405)
        self.assertEqual(self.client.get(url_etapa).status_code, 405)

        resposta = self.client.post(url_sessao)
        sessao_um.refresh_from_db()
        etapa.refresh_from_db()
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(sessao_um.concluida)
        self.assertFalse(etapa.concluida)

        self.client.post(url_etapa)
        sessao_um.refresh_from_db()
        sessao_dois.refresh_from_db()
        etapa.refresh_from_db()
        self.assertTrue(sessao_um.concluida)
        self.assertTrue(sessao_dois.concluida)
        self.assertTrue(etapa.concluida)

        self.client.post(url_etapa)
        sessao_um.refresh_from_db()
        sessao_dois.refresh_from_db()
        etapa.refresh_from_db()
        self.assertFalse(sessao_um.concluida)
        self.assertFalse(sessao_dois.concluida)
        self.assertFalse(etapa.concluida)

    def test_usuario_de_outro_nao_altera_sessao(self):
        etapa = EtapaCronograma.objects.create(
            cronograma=self.cronograma,
            titulo="Etapa 1",
            minutos_estimados=30,
        )
        sessao = SessaoEstudo.objects.create(
            etapa=etapa,
            data=date(2026, 11, 25),
            minutos=30,
        )
        self.client.force_login(self.outro_usuario)

        resposta = self.client.post(
            reverse("cronogramas:sessao_alternar", args=[sessao.pk])
        )

        self.assertEqual(resposta.status_code, 404)
        sessao.refresh_from_db()
        self.assertFalse(sessao.concluida)

    def test_detalhe_gerando_exibe_mensagem_e_polling(self):
        cronograma = self.criar_cronograma(
            self.dono,
            status=Cronograma.Status.GERANDO,
        )

        resposta = self.client.get(
            reverse("cronogramas:detalhe", args=[cronograma.pk])
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(
            resposta,
            "Estamos montando seu cronograma, isso pode levar um minuto...",
        )
        self.assertContains(resposta, "setInterval(consultarStatus, 3000)")
        self.assertContains(
            resposta,
            reverse("cronogramas:status", args=[cronograma.pk]),
        )

    def test_detalhe_falhou_exibe_erro_e_formulario_de_nova_tentativa(self):
        cronograma = self.criar_cronograma(
            self.dono,
            status=Cronograma.Status.FALHOU,
            erro="Não foi possível gerar o cronograma. Tente novamente.",
        )

        resposta = self.client.get(
            reverse("cronogramas:detalhe", args=[cronograma.pk])
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, cronograma.erro)
        self.assertContains(
            resposta,
            reverse("cronogramas:tentar_novamente", args=[cronograma.pk]),
        )
        self.assertContains(resposta, 'name="csrfmiddlewaretoken"')
        self.assertNotContains(resposta, "atrasado")
        self.assertNotContains(resposta, "perdeu")

    def test_detalhe_pronto_exibe_agenda_etapas_aviso_e_fontes(self):
        etapa = EtapaCronograma.objects.create(
            cronograma=self.cronograma,
            titulo="Revisar equações",
            descricao="Estudar os conceitos principais.",
            minutos_estimados=45,
            recursos=[{
                "titulo": "Vídeo recomendado",
                "tipo": "video",
                "url": "https://example.com/recurso",
            }],
        )
        SessaoEstudo.objects.create(
            etapa=etapa,
            data=timezone.localdate(),
            minutos=45,
        )
        self.cronograma.fontes = [{
            "titulo": "Fonte consultada",
            "url": "https://example.com/fonte",
        }]
        self.cronograma.save(update_fields=["fontes", "atualizado_em"])

        resposta = self.client.get(
            reverse("cronogramas:detalhe", args=[self.cronograma.pk])
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Agenda de estudos")
        self.assertContains(resposta, "Revisar equações")
        self.assertContains(resposta, "45 minutos")
        self.assertContains(resposta, "Este cronograma foi preparado")
        self.assertContains(resposta, "https://example.com/fonte")

    def test_lista_mostra_estado_gerando(self):
        self.cronograma.status = Cronograma.Status.GERANDO
        self.cronograma.save(update_fields=["status", "atualizado_em"])

        resposta = self.client.get(reverse("cronogramas:lista"))

        self.assertContains(resposta, "Gerando...")
