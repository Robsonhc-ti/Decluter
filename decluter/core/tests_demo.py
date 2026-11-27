import os
import secrets
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase

from boards.models import Board, Coluna, Tarefa
from cronogramas.models import Cronograma, EtapaCronograma, SessaoEstudo
from projetos.models import MembroProjeto, Projeto


class PopularDemoCommandTests(TestCase):
    def test_comando_cria_dados_com_senha_do_ambiente_e_e_idempotente(self):
        senha = secrets.token_urlsafe(24)
        saida = StringIO()

        with patch.dict(os.environ, {"DEMO_PASSWORD": senha}):
            call_command("popular_demo", stdout=saida)
            call_command("popular_demo", stdout=saida)

        usuario_modelo = get_user_model()
        aluno = usuario_modelo.objects.get(email="demo.aluno@example.invalid")
        colega = usuario_modelo.objects.get(email="demo.colega@example.invalid")
        projeto = Projeto.objects.get(
            criador=aluno,
            nome="Projeto de demonstração",
        )
        cronograma = Cronograma.objects.get(
            usuario=aluno,
            nome="Cronograma de demonstração",
        )

        self.assertTrue(aluno.check_password(senha))
        self.assertTrue(colega.check_password(senha))
        self.assertEqual(usuario_modelo.objects.filter(
            email__endswith="@example.invalid"
        ).count(), 2)
        self.assertEqual(MembroProjeto.objects.filter(projeto=projeto).count(), 2)
        self.assertEqual(Board.objects.filter(projeto=projeto).count(), 1)
        self.assertEqual(Coluna.objects.filter(board__projeto=projeto).count(), 3)
        self.assertEqual(Tarefa.objects.filter(coluna__board__projeto=projeto).count(), 3)
        self.assertEqual(cronograma.status, Cronograma.Status.PRONTO)
        self.assertEqual(EtapaCronograma.objects.filter(cronograma=cronograma).count(), 3)
        self.assertEqual(SessaoEstudo.objects.filter(
            etapa__cronograma=cronograma
        ).count(), 3)
        self.assertIn("Dados de demonstração preparados", saida.getvalue())

    def test_comando_exige_demo_password(self):
        with patch.dict(os.environ, {"DEMO_PASSWORD": ""}):
            with self.assertRaises(CommandError):
                call_command("popular_demo", stdout=StringIO())

        self.assertFalse(Projeto.objects.filter(
            nome="Projeto de demonstração"
        ).exists())
