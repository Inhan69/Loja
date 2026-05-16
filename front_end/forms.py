from django import forms
from .models import Produto, Client
import re

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'codigo', 'quantidade', 'preco']


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilo = 'border-radius: 15px; border: 1px solid #ccc; padding: 10px; background-color: #f0f0f0; text-align: left; font-size: 20px;'
        
        
        for field_name, field in self.fields.items():
            attrs = {
                'style': estilo,
                'class': 'form-control',
                'placeholder': f'Digite o {field_name}...',
                'autocomplete': 'one-time-code',
            }
        
            if field_name == 'nome':
                attrs['autofocus'] = 'autofocus'
            
            field.widget.attrs.update(attrs)


class Edit_ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'quantidade', 'preco']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilo = 'display: block; width: 100%; height: 45px; padding: 10px 15px; border-radius: 10px; border: 1px solid #ddd; background: #f9f9f9; box-sizing: border-box; font-size: 15px;'
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'style': estilo})


class ClientForm(forms.ModelForm):
    cpf = forms.CharField(max_length=14)
    telefone = forms.CharField(max_length=16)

    class Meta:
        model = Client
        fields = ['nome', 'cpf', 'telefone', 'rua', 'bairro', 'dt_nascimento', 'numero']

    def clean_cpf(self):
        cpf = self.cleaned_data.get("cpf", "")
        cpf = re.sub(r"\D", "", cpf)

        if len(cpf) != 11:
            raise forms.ValidationError("CPF deve conter exatamente 11 dígitos.")
        return cpf

    def clean_telefone(self):
        telefone = self.cleaned_data.get("telefone", "")
        telefone = re.sub(r"\D", "", telefone)

        if len(telefone) != 11:
            raise forms.ValidationError("Telefone deve conter exatamente 11 dígitos (DDD + número).")
        return telefone