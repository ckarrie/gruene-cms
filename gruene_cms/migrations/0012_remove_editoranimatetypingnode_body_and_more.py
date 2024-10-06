# Generated by Django 5.1.1 on 2024-10-06 14:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0035_auto_20230822_2208_squashed_0036_auto_20240311_1028'),
        ('gruene_cms', '0011_editoranimatetypingnode'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='editoranimatetypingnode',
            name='body',
        ),
        migrations.AlterField(
            model_name='editoranimatetypingnode',
            name='cmsplugin_ptr',
            field=models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='%(app_label)s_%(class)s', serialize=False, to='cms.cmsplugin'),
        ),
    ]
