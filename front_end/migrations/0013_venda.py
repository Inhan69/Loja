from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("front_end", "0012_client_dt_nascimento"),
    ]

    operations = [
        migrations.CreateModel(
            name="Venda",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantidade", models.DecimalField(decimal_places=3, max_digits=10)),
                ("desconto", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("tipo_pagamento", models.CharField(choices=[("dinheiro", "Dinheiro"), ("pix", "PIX"), ("cartao_credito", "Cartão de Crédito"), ("cartao_debito", "Cartão de Débito")], max_length=20)),
                ("total", models.DecimalField(decimal_places=2, max_digits=12)),
                ("dt_venda", models.DateTimeField(auto_now_add=True)),
                ("produto", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="vendas", to="front_end.produto")),
            ],
        ),
    ]
