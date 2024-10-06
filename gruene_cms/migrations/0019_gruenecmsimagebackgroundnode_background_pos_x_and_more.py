# Generated by Django 5.1.1 on 2024-10-06 20:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gruene_cms', '0018_chartjsnode_dataset_history_hours'),
    ]

    operations = [
        migrations.AddField(
            model_name='gruenecmsimagebackgroundnode',
            name='background_pos_x',
            field=models.CharField(choices=[('center', 'Center'), ('left', 'Left'), ('right', 'Right')], default='center', max_length=10),
        ),
        migrations.AddField(
            model_name='gruenecmsimagebackgroundnode',
            name='background_pos_y',
            field=models.CharField(choices=[('center', 'Center'), ('top', 'Top'), ('bottom', 'Bottom')], default='top', max_length=10),
        ),
        migrations.AddField(
            model_name='gruenecmsimagebackgroundnode',
            name='background_size',
            field=models.CharField(choices=[('auto', 'Auto'), ('contain', 'Contain'), ('cover', 'Cover')], default='cover', max_length=10),
        ),
        migrations.AlterField(
            model_name='newsitem',
            name='content_rendered',
            field=models.TextField(blank=True, null=True),
        ),
    ]
