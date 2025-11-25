from django import forms
from .models import Item
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class ItemForm(forms.ModelForm):
    adicionar_quantidade = forms.IntegerField(
        label="Adicionar Itens",
        required=False,
        initial=0,
        min_value=0,    # Não permite adicionar valores negativos
        widget=forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'})
    )

    class Meta:
        model = Item
        fields = ['nome', 'codigo', 'categoria', 'disponivel', 'capacidade_maxima', 'valor', 'localizacao', 'imagem']

        widgets = {
            'nome': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'codigo': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'categoria': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'disponivel': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'capacidade_maxima': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'valor': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg', 'step': '0.01'}),
            'localizacao': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'imagem': forms.ClearableFileInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Se o item já existe (tem pk/id), bloqueia o campo 'disponivel' (modo edição)
        if self.instance.pk:
            self.fields['disponivel'].widget.attrs['readonly'] = True
            self.fields['disponivel'].widget.attrs['class'] += ' bg-gray-100 text-gray-500 cursor-not-allowed'
        else:
            if 'readonly' in self.fields['disponivel'].widget.attrs:
                del self.fields['disponivel'].widget.attrs['readonly']
            self.fields['adicionar_quantidade'].widget = forms.HiddenInput()

        # Percorre todos os campos e força required=True, exceto no 'adicionar_quantidade'
        for field_name, field in self.fields.items():
            if field_name != 'adicionar_quantidade':
                field.required = True

                label_atual = field.label or field_name.replace('_', ' ').capitalize()
                if not label_atual.endswith('*'):
                    field.label = f"{label_atual} *"

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

class PerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'block w-full rounded-md border-gray-200 shadow-sm py-2 px-3'}),
            'last_name': forms.TextInput(attrs={'class': 'block w-full rounded-md border-gray-200 shadow-sm py-2 px-3'}),
            'email': forms.EmailInput(attrs={'class': 'block w-full rounded-md border-gray-200 shadow-sm py-2 px-3'}),
        }
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'Email',
        }