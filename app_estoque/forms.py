# app_estoque/forms.py

from django import forms
from .models import Item
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class ItemForm(forms.ModelForm):
    adicionar_quantidade = forms.IntegerField(
        label="Adicionar Itens",
        required=False, # Não é obrigatório preencher
        initial=0,      # Começa com o valor 0
        min_value=0,    # Não permite adicionar valores negativos
        widget=forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'})
    )

    class Meta:
        model = Item
        # Escolha os campos do modelo 'Item' que você quer no formulário
        fields = ['nome', 'codigo', 'categoria', 'disponivel', 'capacidade_maxima', 'valor', 'imagem']
        
        # Opcional: Adiciona classes CSS para estilizar os campos
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'codigo': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'categoria': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'disponivel': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'capacidade_maxima': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'valor': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg', 'step': '0.01'}),
            'imagem': forms.ClearableFileInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Torna o campo 'disponivel' somente leitura (desabilitado para edição)
        self.fields['disponivel'].widget.attrs['readonly'] = True
        self.fields['disponivel'].widget.attrs['class'] = 'w-full p-2 border bg-gray-100 text-gray-500 rounded-lg'
    
class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text='Obrigatório.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Obrigatório.')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Define as classes de estilo para todos os campos
        default_field_classes = 'w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-600 focus:border-blue-600'
        
        # Aplica as classes e placeholders
        self.fields['first_name'].widget.attrs.update({'class': default_field_classes, 'placeholder': 'Digite seu nome'})
        self.fields['last_name'].widget.attrs.update({'class': default_field_classes, 'placeholder': 'Digite seu sobrenome'})
        self.fields['username'].widget.attrs.update({'class': default_field_classes, 'placeholder': 'Digite seu RE'})
        self.fields['password1'].widget.attrs.update({'class': default_field_classes, 'placeholder': 'Digite sua senha'})
        self.fields['password2'].widget.attrs.update({'class': default_field_classes, 'placeholder': 'Confirme sua senha'})
        
        # Customiza os nomes e remove os textos de ajuda
        self.fields['username'].label = "RE (Registro de empregado)"
        self.fields['username'].help_text = None
        self.fields['password1'].label = "Senha"
        self.fields['password1'].help_text = None
        self.fields['password2'].label = "Confirmação da senha"
        self.fields['password2'].help_text = None

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user