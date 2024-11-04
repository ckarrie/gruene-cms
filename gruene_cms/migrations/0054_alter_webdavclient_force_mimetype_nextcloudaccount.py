# Generated by Django 5.1.2 on 2024-10-30 10:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gruene_cms', '0053_category_is_public'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='webdavclient',
            name='force_mimetype',
            field=models.CharField(blank=True, choices=[(None, 'Use file extensions'), ('application/csv', '.csv | Comma separated'), ('text/x-vcard', '.vcf | Contacts'), ('text/x-vcalendar', '.vcs | Calendar')], max_length=255, null=True),
        ),
        migrations.CreateModel(
            name='NextCloudAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nextcloud_username', models.CharField(max_length=50)),
                ('nextcloud_app_password', models.CharField(max_length=255)),
                ('nextcloud_url', models.CharField(default='https://wolke.netzbegruenung.de', help_text='Without tailing slash', max_length=255)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
