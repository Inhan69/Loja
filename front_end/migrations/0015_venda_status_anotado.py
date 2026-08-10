from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("front_end", "0014_venda_cliente_observacao"),
    ]

    operations = [
        migrations.AddField(
            model_name="venda",
            name="status",
            field=models.CharField(
                choices=[
                    ("anotado", "Anotado"),
                    ("pago", "Pago"),
                    ("devolvido", "Devolvido"),
                ],
                default="pago",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="venda",
            name="tipo_pagamento",
            field=models.CharField(
                choices=[
                    ("dinheiro", "Dinheiro"),
                    ("pix", "PIX"),
                    ("cartao_credito", "Cartão de Crédito"),
                    ("cartao_debito", "Cartão de Débito"),
                    ("anotado", "Anotado (fiado)"),
                ],
                max_length=20,
            ),
        ),
    ]
