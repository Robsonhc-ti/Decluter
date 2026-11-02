from django import forms

from .models import Cronograma


class CronogramaForm(forms.ModelForm):
    class Meta:
        model = Cronograma
        fields = ["nome", "tema", "tempo_por_dia", "nivel", "complemento"]


class FaculdadeForm(forms.ModelForm):
    class Meta:
        model = Cronograma
        fields = ["instituicao", "curso", "tempo_por_dia", "nivel", "complemento"]
        labels = {
            "instituicao": "Faculdade",
            "curso": "Curso",
            "tempo_por_dia": "Quanto tempo quer estudar por dia?",
            "complemento": "Complemento (opcional)",
        }
        widgets = {
            "instituicao": forms.TextInput(attrs={"autocomplete": "off"}),
            "curso": forms.TextInput(attrs={"autocomplete": "off"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["instituicao"].required = True
        self.fields["curso"].required = True


class EnemForm(forms.ModelForm):
    class Meta:
        model = Cronograma
        fields = ["tempo_por_dia", "nivel", "complemento"]
        labels = {
            "tempo_por_dia": "Quanto tempo quer estudar por dia?",
            "complemento": "Complemento (opcional)",
        }