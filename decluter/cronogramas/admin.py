from django.contrib import admin
from .models import Cronograma, EtapaCronograma


@admin.register(Cronograma)
class CronogramaAdmin(admin.ModelAdmin):
    list_display = ["nome", "usuario", "tema", "nivel"]


@admin.register(EtapaCronograma)
class EtapaCronogramaAdmin(admin.ModelAdmin):
    list_display = ["titulo", "cronograma", "concluida", "ordem"]