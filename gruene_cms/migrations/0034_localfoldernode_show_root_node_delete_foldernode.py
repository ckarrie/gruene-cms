# Generated by Django 5.1.1 on 2024-10-11 15:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gruene_cms', '0033_remove_localfoldernode_local_path_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='localfoldernode',
            name='show_root_node',
            field=models.BooleanField(default=False),
        ),
        migrations.DeleteModel(
            name='FolderNode',
        ),
    ]