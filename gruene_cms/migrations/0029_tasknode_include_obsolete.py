# Generated by Django 5.1.1 on 2024-10-10 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gruene_cms', '0028_taskitem_priority'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasknode',
            name='include_obsolete',
            field=models.BooleanField(default=False),
        ),
    ]