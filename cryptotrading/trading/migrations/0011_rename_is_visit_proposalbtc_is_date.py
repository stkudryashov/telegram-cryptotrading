# Generated by Django 3.2 on 2021-04-07 23:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0010_proposalbtc_is_visit'),
    ]

    operations = [
        migrations.RenameField(
            model_name='proposalbtc',
            old_name='is_visit',
            new_name='is_date',
        ),
    ]