from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class ConfiguracoesViewTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="aluno",
            email="aluno@example.com",
            password="Senha-atual-123!",
        )
        self.url = reverse("usuarios:configuracoes")

    def test_pagina_exige_login(self):
        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("usuarios:auth"), resposta["Location"])

    def test_altera_senha_com_senha_atual_correta_e_mantem_login(self):
        self.client.force_login(self.usuario)

        resposta = self.client.post(
            self.url,
            {
                "old_password": "Senha-atual-123!",
                "new_password1": "Senha-nova-456!",
                "new_password2": "Senha-nova-456!",
                "alterar_senha": "1",
            },
            follow=True,
        )

        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("Senha-nova-456!"))
        self.assertTrue(resposta.wsgi_request.user.is_authenticated)
        self.assertContains(resposta, "Senha alterada com sucesso")
        html = resposta.content.decode()
        inicio_alerta = html.index('<div role="alert" aria-live="assertive">')
        fim_alerta = html.index("</div>", inicio_alerta)
        self.assertIn(
            "Senha alterada com sucesso",
            html[inicio_alerta:fim_alerta],
        )

    def test_senha_atual_incorreta_nao_altera_senha(self):
        self.client.force_login(self.usuario)

        resposta = self.client.post(
            self.url,
            {
                "old_password": "senha-incorreta",
                "new_password1": "Senha-nova-456!",
                "new_password2": "Senha-nova-456!",
                "alterar_senha": "1",
            },
        )

        self.usuario.refresh_from_db()
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(self.usuario.check_password("Senha-atual-123!"))
        self.assertIn("old_password", resposta.context["senha_form"].errors)
        self.assertContains(resposta, "Senha atual incorreta")
        html = resposta.content.decode()
        inicio_alerta = html.index('<div role="alert" aria-live="assertive">')
        fim_alerta = html.index("</div>", inicio_alerta)
        self.assertIn(
            "Senha atual incorreta. Confira e tente novamente.",
            html[inicio_alerta:fim_alerta],
        )
        self.assertNotContains(resposta, "Senha alterada com sucesso")

    def test_formularios_reposicionam_a_pagina_nas_secoes(self):
        self.client.force_login(self.usuario)

        resposta = self.client.get(self.url)

        self.assertContains(resposta, '<section id="perfil"')
        self.assertContains(resposta, '<form method="post" action="#perfil">')
        self.assertContains(resposta, '<section id="seguranca"')
        self.assertContains(
            resposta,
            '<form method="post" action="#seguranca">',
        )

    def test_edita_nome_e_sobrenome(self):
        self.client.force_login(self.usuario)

        resposta = self.client.post(
            self.url,
            {
                "first_name": "Ana",
                "last_name": "Silva",
                "salvar_perfil": "1",
            },
            follow=True,
        )

        self.usuario.refresh_from_db()
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.usuario.first_name, "Ana")
        self.assertEqual(self.usuario.last_name, "Silva")
        self.assertContains(resposta, "Seu perfil foi atualizado.")
