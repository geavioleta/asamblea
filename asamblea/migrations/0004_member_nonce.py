# Generated by Django 3.0 on 2019-12-12 03:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asamblea', '0003_auto_20191212_0000'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='nonce',
            field=models.CharField(default='', max_length=100),
        ),
    ]
