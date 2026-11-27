from django import forms

from .models import Cronograma


DIAS_DA_SEMANA = [
    (0, "Segunda-feira"),
    (1, "Terça-feira"),
    (2, "Quarta-feira"),
    (3, "Quinta-feira"),
    (4, "Sexta-feira"),
    (5, "Sábado"),
    (6, "Domingo"),
]


def _campo_dias_estudo():
    return forms.TypedMultipleChoiceField(
        choices=DIAS_DA_SEMANA,
        coerce=int,
        initial=[0, 1, 2, 3, 4],
        required=True,
        error_messages={"required": "Selecione pelo menos um dia de estudo."},
        widget=forms.CheckboxSelectMultiple,
    )


class CronogramaForm(forms.ModelForm):
    dias_estudo = _campo_dias_estudo()

    class Meta:
        model = Cronograma
        fields = [
            "nome",
            "tema",
            "tempo_por_dia",
            "nivel",
            "complemento",
            "dias_estudo",
        ]


class FaculdadeForm(forms.ModelForm):
    dias_estudo = _campo_dias_estudo()

    class Meta:
        model = Cronograma
        fields = [
            "instituicao",
            "curso",
            "tempo_por_dia",
            "nivel",
            "complemento",
            "dias_estudo",
        ]
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
    dias_estudo = _campo_dias_estudo()

    class Meta:
        model = Cronograma
        fields = ["tempo_por_dia", "nivel", "complemento", "dias_estudo"]
        labels = {
            "tempo_por_dia": "Quanto tempo quer estudar por dia?",
            "complemento": "Complemento (opcional)",
        }