from django import forms

from .models import Tarefa


class TarefaForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        fields = ["titulo", "descricao", "prioridade", "prazo", "responsavel"]
        widgets = {
            "prazo": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, projeto, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsavel"].queryset = self.fields["responsavel"].queryset.filter(
            vinculos_projetos__projeto=projeto
        )