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