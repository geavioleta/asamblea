# Generated by Django 3.0 on 2019-12-12 00:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('asamblea', '0002_auto_20191211_1659'),
    ]

    operations = [
        migrations.RenameField(
            model_name='member',
            old_name='profileCreated',
            new_name='profile_created',
        ),
    ]
