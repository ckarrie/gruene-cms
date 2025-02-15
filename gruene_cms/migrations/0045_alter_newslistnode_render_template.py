# Generated by Django 5.1.2 on 2024-10-23 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gruene_cms', '0044_newsitem_newsfeedreader_external_image_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newslistnode',
            name='render_template',
            field=models.CharField(choices=[('tiles', 'Tiles, Image and Summary'), ('table', 'Table, Image and Summary'), ('card_v1', 'Cards, Variant 1'), ('full', 'Full')], default='tiles', max_length=20),
        ),
    ]
