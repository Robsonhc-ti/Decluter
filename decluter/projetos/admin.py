from django.contrib import admin

from .models import MembroProjeto, Projeto


class MembroProjetoInline(admin.TabularInline):
    model = MembroProjeto
    extra = 1


@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ("nome", "criador", "criado_em")
    search_fields = ("nome",)
    inlines = [MembroProjetoInline]


@admin.register(MembroProjeto)
class MembroProjetoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "projeto", "papel", "ultimo_acesso_em")
    list_filter = ("papel",)