# Generated by Django 5.0.6 on 2025-02-11 03:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notebook', '0003_rename_description_notebook_overview'),
    ]

    operations = [
        migrations.AddField(
            model_name='notebook',
            name='cover',
            field=models.ImageField(blank=True, null=True, upload_to='notebook_covers/'),
        ),
    ]
