from django.shortcuts import render


def login_view(request):
    return render(
        request,
        "usuarios/login.html"
    )


def cadastro_view(request):
    return render(
        request,
        "usuarios/cadastro.html"
    )

def perfil_view(request):
    
    return render(request, 'perfil.html')
