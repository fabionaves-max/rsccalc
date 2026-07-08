from django import forms
from .models import AtividadeComprovada

class AtividadeComprovadaForm(forms.ModelForm):
    class Meta:
        model = AtividadeComprovada
        # Adicionamos o descricao_atividade na lista de campos
        fields = ['criterio', 'quantidade', 'descricao_atividade', 'arquivo_comprovante']
        widgets = {
            'criterio': forms.Select(attrs={'class': 'form-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            # Configuração visual da caixa de texto (Textarea)
            'descricao_atividade': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descreva sua atuação, os resultados obtidos e as competências desenvolvidas...'
            }),
            'arquivo_comprovante': forms.FileInput(attrs={'class': 'form-control'}),
        }