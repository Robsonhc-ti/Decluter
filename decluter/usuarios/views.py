from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import AlterarSenhaForm, CadastroForm, PerfilForm


def auth_view(request):
    erro = None

    if request.method == "POST":
        if "criar_conta" in request.POST:
            form = CadastroForm(request.POST)
            if form.is_valid():
                usuario = form.save()
                login(request, usuario)
                return redirect("dashboard")
            else:
                erro = form.errors.as_text()
        else:
            email = request.POST.get("email")
            senha = request.POST.get("password1")
            usuario = authenticate(request, username=email, password=senha)
            if usuario is not None:
                login(request, usuario)
                return redirect("dashboard")
            else:
                erro = "Email ou senha incorretos."

    return render(request, "usuarios/auth.html", {"erro": erro})


@login_required
def logout_view(request):
    logout(request)
    return redirect("usuarios:auth")


@login_required
def configuracoes_view(request):
    perfil_form = PerfilForm(instance=request.user)
    senha_form = AlterarSenhaForm(request.user)

    if request.method == "POST":
        if "salvar_perfil" in request.POST:
            perfil_form = PerfilForm(request.POST, instance=request.user)
            if perfil_form.is_valid():
                perfil_form.save()
                messages.success(request, "Seu perfil foi atualizado.")
                return redirect(f"{reverse('usuarios:configuracoes')}#perfil")
            messages.error(request, "Confira os campos do perfil e tente novamente.")
        elif "alterar_senha" in request.POST:
            senha_form = AlterarSenhaForm(request.user, request.POST)
            if senha_form.is_valid():
                usuario = senha_form.save()
                update_session_auth_hash(request, usuario)
                messages.success(request, "Senha alterada com sucesso")
                return redirect(f"{reverse('usuarios:configuracoes')}#seguranca")
            if "old_password" in senha_form.errors:
                messages.error(
                    request,
                    "Senha atual incorreta. Confira e tente novamente.",
                )
            else:
                messages.error(request, "Confira os campos da senha e tente novamente.")

    return render(request, "usuarios/configuracoes.html", {
        "perfil_form": perfil_form,
        "senha_form": senha_form,
    })
