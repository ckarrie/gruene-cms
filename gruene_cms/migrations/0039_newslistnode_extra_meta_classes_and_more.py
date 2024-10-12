# Generated by Django 5.1.1 on 2024-10-12 13:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gruene_cms', '0038_newslistnode_show_date_newslistnode_show_feed_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='newslistnode',
            name='extra_meta_classes',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='newslistnode',
            name='show_newsitem_separator',
            field=models.BooleanField(default=False),
        ),
    ]