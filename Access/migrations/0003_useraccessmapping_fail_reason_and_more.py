# Generated by Django 4.1.3 on 2023-02-19 12:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Access', '0002_useridentity_delete_gitacces_remove_user_gitusername_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraccessmapping',
            name='fail_reason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='groupaccessmapping',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='group_access_mapping', to='Access.groupv2'),
        ),
    ]
