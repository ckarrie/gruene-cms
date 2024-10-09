# Generated by Django 5.1.1 on 2024-10-07 14:58

import django.db.models.deletion
import filer.fields.image
from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gruene_cms', '0021_newslistnode_title_h'),
        migrations.swappable_dependency(settings.FILER_IMAGE_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='logo',
            field=filer.fields.image.FilerImageField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.FILER_IMAGE_MODEL),
        ),
    ]