# Generated by Django 5.1.2 on 2024-11-05 00:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gruene_cms', '0056_newsfeedreader_active_auto_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='url',
            field=models.URLField(blank=True, null=True),
        ),
    ]
