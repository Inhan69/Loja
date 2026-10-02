from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("front_end", "0019_client_numero_null"),
    ]

    operations = [
        migrations.AddField(
            model_name="venda",
            name="acrescimo",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
    ]
