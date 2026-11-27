from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm

from .models import Usuario


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ["first_name", "last_name"]
        labels = {
            "first_name": "Nome",
            "last_name": "Sobrenome",
        }


class AlterarSenhaForm(PasswordChangeForm):
    error_messages = {
        **PasswordChangeForm.error_messages,
        "password_incorrect": "Senha atual incorreta. Confira e tente novamente.",
    }


class CadastroForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ["username", "email"]