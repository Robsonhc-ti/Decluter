from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Cronograma, EtapaCronograma, SessaoEstudo


class ExclusaoCronogramaTests(TestCase):
    def setUp(self):
        usuario_modelo = get_user_model()
        self.dono = usuario_modelo.objects.create_user(
            username="dono-exclusao",
            email="dono@example.com",
            password="senha-de-teste",
        )
        self.outro_usuario = usuario_modelo.objects.create_user(
            username="outro-exclusao",
            email="outro@example.com",
            password="senha-de-teste",
        )
        self.cronograma = Cronograma.objects.create(
            usuario=self.dono,
            nome="Plano para excluir",
            tema="Matemática",
            tempo_por_dia="1h",
            nivel="iniciante",
            status=Cronograma.Status.PRONTO,
        )
        self.etapa = EtapaCronograma.objects.create(
            cronograma=self.cronograma,
            titulo="Etapa a excluir",
            minutos_estimados=30,
        )
        self.sessao = SessaoEstudo.objects.create(
            etapa=self.etapa,
            data=date(2026, 11, 25),
            minutos=30,
        )
        self.url = reverse("cronogramas:excluir", args=[self.cronograma.pk])

    def test_dono_confirma_e_exclui_em_cascata(self):
        self.client.force_login(self.dono)

        confirmacao = self.client.get(self.url)
        self.assertEqual(confirmacao.status_code, 200)
        self.assertContains(confirmacao, "Confirma a exclusão")
        self.assertTrue(Cronograma.objects.filter(pk=self.cronograma.pk).exists())

        resposta = self.client.post(self.url, follow=True)

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Plano para excluir")
        self.assertContains(resposta, "excluído com sucesso.")
        self.assertFalse(Cronograma.objects.filter(pk=self.cronograma.pk).exists())
        self.assertFalse(EtapaCronograma.objects.filter(pk=self.etapa.pk).exists())
        self.assertFalse(SessaoEstudo.objects.filter(pk=self.sessao.pk).exists())

    def test_usuario_que_nao_e_dono_recebe_404(self):
        self.client.force_login(self.outro_usuario)

        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url).status_code, 404)
        self.assertTrue(Cronograma.objects.filter(pk=self.cronograma.pk).exists())
