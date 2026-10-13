from django.contrib import admin
from .models import Board, Coluna, Tarefa, Comentario

admin.site.register(Board)
admin.site.register(Coluna)
admin.site.register(Tarefa)
admin.site.register(Comentario)