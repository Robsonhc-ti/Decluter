from django.contrib import admin
from .models import Cronograma, EtapaCronograma, SessaoEstudo


@admin.register(Cronograma)
class CronogramaAdmin(admin.ModelAdmin):
    list_display = ["nome", "usuario", "tema", "nivel", "status"]


@admin.register(EtapaCronograma)
class EtapaCronogramaAdmin(admin.ModelAdmin):
    list_display = [
        "titulo",
        "cronograma",
        "concluida",
        "ordem",
        "minutos_estimados",
    ]


@admin.register(SessaoEstudo)
class SessaoEstudoAdmin(admin.ModelAdmin):
    list_display = ["etapa", "data", "minutos", "concluida"]