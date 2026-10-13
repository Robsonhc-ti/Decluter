from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import CadastroForm


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