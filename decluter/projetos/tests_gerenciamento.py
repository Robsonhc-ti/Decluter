from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import MembroProjeto, Projeto


class GerenciamentoProjetoTests(TestCase):
    def setUp(self):
        usuario_modelo = get_user_model()
        self.admin = usuario_modelo.objects.create_user(
            username="admin-projeto",
            email="admin@example.com",
            password="senha-de-teste",
        )
        self.membro = usuario_modelo.objects.create_user(
            username="membro-projeto",
            email="membro@example.com",
            password="senha-de-teste",
        )
        self.estranho = usuario_modelo.objects.create_user(
            username="estranho-projeto",
            email="estranho@example.com",
            password="senha-de-teste",
        )
        self.projeto = Projeto.objects.create(
            nome="Projeto inicial",
            descricao="Descrição inicial",
            criador=self.admin,
        )
        MembroProjeto.objects.create(
            projeto=self.projeto,
            usuario=self.admin,
            papel=MembroProjeto.Papel.ADMIN,
        )
        MembroProjeto.objects.create(
            projeto=self.projeto,
            usuario=self.membro,
            papel=MembroProjeto.Papel.MEMBRO,
        )
        self.url_editar = reverse("projetos:editar", args=[self.projeto.pk])
        self.url_excluir = reverse("projetos:excluir", args=[self.projeto.pk])

    def test_admin_edita_projeto_e_recebe_mensagem(self):
        self.client.force_login(self.admin)

        resposta = self.client.post(
            self.url_editar,
            {"nome": "Projeto atualizado", "descricao": "Nova descrição"},
            follow=True,
        )

        self.projeto.refresh_from_db()
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.projeto.nome, "Projeto atualizado")
        self.assertEqual(self.projeto.descricao, "Nova descrição")
        self.assertContains(resposta, "Projeto atualizado com sucesso.")

    def test_admin_confirma_exclusao_por_post(self):
        self.client.force_login(self.admin)

        confirmacao = self.client.get(self.url_excluir)
        self.assertEqual(confirmacao.status_code, 200)
        self.assertContains(confirmacao, "Confirma a exclusão")
        self.assertTrue(Projeto.objects.filter(pk=self.projeto.pk).exists())

        resposta = self.client.post(self.url_excluir, follow=True)

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Projeto.objects.filter(pk=self.projeto.pk).exists())
        self.assertContains(resposta, "Projeto inicial")
        self.assertContains(resposta, "excluído com sucesso.")

    def test_membro_nao_pode_editar_ou_excluir(self):
        self.client.force_login(self.membro)

        self.assertEqual(self.client.get(self.url_editar).status_code, 403)
        self.assertEqual(self.client.post(self.url_editar, {
            "nome": "Alteração não autorizada",
            "descricao": "",
        }).status_code, 403)
        self.assertEqual(self.client.get(self.url_excluir).status_code, 403)
        self.assertEqual(self.client.post(self.url_excluir).status_code, 403)
        self.assertTrue(Projeto.objects.filter(pk=self.projeto.pk).exists())

    def test_nao_membro_recebe_404_em_edicao_e_exclusao(self):
        self.client.force_login(self.estranho)

        self.assertEqual(self.client.get(self.url_editar).status_code, 404)
        self.assertEqual(self.client.post(self.url_editar, {
            "nome": "Alteração não autorizada",
            "descricao": "",
        }).status_code, 404)
        self.assertEqual(self.client.get(self.url_excluir).status_code, 404)
        self.assertEqual(self.client.post(self.url_excluir).status_code, 404)
        self.assertTrue(Projeto.objects.filter(pk=self.projeto.pk).exists())
