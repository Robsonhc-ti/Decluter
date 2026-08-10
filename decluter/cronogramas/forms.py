from django import forms
from .models import Cronograma


class CronogramaForm(forms.ModelForm):
    class Meta:
        model = Cronograma
        fields = ["nome", "tema", "tempo_por_dia", "nivel", "complemento"]