# Generated by Django 5.1.1 on 2024-10-27 16:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gruene_cms', '0046_alter_newslistnode_render_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='webdavclient',
            name='entry_path_title',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='webdavclient',
            name='force_mimetype',
            field=models.CharField(blank=True, choices=[(None, 'Use file extensions'), ('application/csv', '.csv'), ('text/x-vcard', '.vcf'), ('text/x-vcalendar', '.vcs')], max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='webdavclient',
            name='title',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
