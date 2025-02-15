# Generated by Django 5.1.1 on 2024-10-28 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gruene_cms', '0050_newslistnode_col_config'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newslistnode',
            name='col_config',
            field=models.CharField(blank=True, choices=[(None, 'All same width'), ('4', 'All 4 cols'), ('6', 'All 6 cols'), ('12', 'All 12 cols'), ('12,6', 'First 12, others 6 cols'), ('12,8,4,6', 'First 12, second 8, third 4, others 6 cols'), ('12,4,8,6', 'First 12, second 4, third 8, others 6 cols'), ('12,9,3,6', 'First 12, second 9, third 3, others 6 cols'), ('12,4,4,4,6', 'First 12, second 4 (until fourth), others 6 cols')], max_length=15, null=True),
        ),
    ]
