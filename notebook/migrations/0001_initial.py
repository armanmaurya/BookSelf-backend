# Generated by Django 5.0.6 on 2025-06-23 03:25

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Notebook',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=100)),
                ('name', models.CharField(max_length=100)),
                ('overview', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cover', models.ImageField(blank=True, null=True, upload_to='notebook_covers/')),
            ],
        ),
    ]
