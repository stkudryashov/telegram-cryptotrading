# Generated by Django 3.2 on 2021-04-07 19:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0003_alter_proposalbtc_point_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposalbtc',
            name='is_point',
            field=models.BooleanField(default=False),
        ),
    ]