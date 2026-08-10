from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    path("entrar/", views.auth_view, name="auth"),
]