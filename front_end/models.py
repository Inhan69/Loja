from django.db import models
from django.core.validators import MaxLengthValidator

class Produto(models.Model):
    nome = models.CharField(max_length=120)
    codigo = models.CharField(unique=True, max_length=4)
    quantidade = models.DecimalField(max_digits=10, decimal_places=3)
    preco = models.DecimalField(max_digits=12, decimal_places=2)
    dt_adicao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome

class Client(models.Model):
    nome = models.CharField(max_length=40)
    cpf = models.CharField("CPF", max_length=11, unique=True)
    telefone = models.CharField(max_length=11, unique=True) 
    rua = models.CharField(max_length=30)
    bairro = models.CharField(max_length=20)
    dt_nascimento = models.DateField(null=True, blank=True) 
    numero = models.PositiveIntegerField("Número")
    dt_criacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome

class Venda(models.Model):
    PAGAMENTO_CHOICES = [
        ("dinheiro", "Dinheiro"),
        ("pix", "PIX"),
        ("cartao_credito", "Cartão de Crédito"),
        ("cartao_debito", "Cartão de Débito"),
        ("anotado", "Anotado (fiado)"),
    ]

    STATUS_CHOICES = [
        ("anotado", "Anotado"),
        ("pago", "Pago"),
        ("devolvido", "Devolvido"),
    ]

    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name="vendas")
    cliente = models.ForeignKey(
        Client, on_delete=models.SET_NULL, null=True, blank=True, related_name="vendas"
    )
    observacao = models.CharField(max_length=200, blank=True, default="")
    quantidade = models.DecimalField(max_digits=10, decimal_places=3)
    desconto = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tipo_pagamento = models.CharField(max_length=20, choices=PAGAMENTO_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pago")
    total = models.DecimalField(max_digits=12, decimal_places=2)
    dt_venda = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.produto.nome} - R${self.total}"