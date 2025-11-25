from django.db import models
from django.contrib.auth.models import User

class Item(models.Model):
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, unique=True)
    categoria = models.CharField(max_length=50)
    disponivel = models.PositiveIntegerField(default=0)
    capacidade_maxima = models.PositiveIntegerField(default=100, help_text="Quantidade que representa 100% do estoque.")
    localizacao = models.CharField(max_length=100, blank=True, help_text="Ex: Corredor A, Prateleira 3")
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Valor monetário da peça (ex: 150.75)"
    )
    imagem = models.ImageField(upload_to='itens/', blank=True, null=True)

    def __str__(self):
        return f"{self.nome} ({self.codigo})"

    @property
    def percentual_disponivel(self):
        if self.capacidade_maxima == 0:
            return 0
        # Calcula a porcentagem e arredonda
        return round((self.disponivel / self.capacidade_maxima) * 100)



class Retirada(models.Model):

    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADA', 'Aprovada'),
        ('RECUSADA', 'Recusada'),
    ]

    """ Representa um único evento de retirada de múltiplos itens. """
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='retiradas')
    data_retirada = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDENTE')
    motivo_recusa = models.TextField(blank=True, null=True, help_text="Justificativa se a retirada for recusada.")

    def __str__(self):
        return f"Retirada por {self.usuario.username} em {self.data_retirada.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        ordering = ['-data_retirada'] # Ordena as retiradas da mais nova para a mais antiga

    @property
    def valor_total(self):
        return sum(
            item_retirado.quantidade * item_retirado.item.valor
            for item_retirado in self.itens_retirados.all()
        )

class ItemRetirado(models.Model):
    """ Representa um item específico dentro de uma retirada, com sua quantidade. """
    retirada = models.ForeignKey(Retirada, on_delete=models.CASCADE, related_name='itens_retirados')
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantidade}x {self.item.nome} na {self.retirada}"

class Notificacao(models.Model):
    """ Representa uma notificação para um usuário. """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificacoes')
    retirada_associada = models.ForeignKey(Retirada, on_delete=models.CASCADE, null=True, blank=True)
    mensagem = models.CharField(max_length=255)
    data_criacao = models.DateTimeField(auto_now_add=True)
    lida = models.BooleanField(default=False)

    def __str__(self):
        return f"Notificação para {self.usuario.username}: {self.mensagem}"

    class Meta:
        ordering = ['-data_criacao'] # Mostra as mais novas primeiro