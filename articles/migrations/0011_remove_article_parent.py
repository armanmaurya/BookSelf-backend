# Generated by Django 5.0.6 on 2025-02-18 09:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0010_article_likes'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='article',
            name='parent',
        ),
    ]
