from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("front_end", "0013_venda"),
    ]

    operations = [
        migrations.AddField(
            model_name="venda",
            name="cliente",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="vendas",
                to="front_end.client",
            ),
        ),
        migrations.AddField(
            model_name="venda",
            name="observacao",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
    ]
