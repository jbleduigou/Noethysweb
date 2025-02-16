# Generated by Django 4.0a1 on 2021-10-09 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_alter_utilisateur_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='individu',
            name='info_garde',
            field=models.TextField(blank=True, null=True, verbose_name='Information sur la garde'),
        ),
        migrations.AddField(
            model_name='individu',
            name='situation_familiale',
            field=models.CharField(blank=True, choices=[(1, 'Célibataire'), (2, 'Marié'), (3, 'Divorcé'), (4, 'Veuf'), (5, 'Concubinage'), (6, 'Séparé'), (7, 'Pacsé'), (8, 'Union libre'), (9, 'Autre')], max_length=100, null=True, verbose_name='Situation familiale'),
        ),
        migrations.AddField(
            model_name='individu',
            name='type_garde',
            field=models.CharField(blank=True, choices=[(1, 'Mère'), (2, 'Père'), (3, 'Garde alternée'), (4, 'Autre personne')], max_length=100, null=True, verbose_name='Type de garde'),
        ),
    ]
