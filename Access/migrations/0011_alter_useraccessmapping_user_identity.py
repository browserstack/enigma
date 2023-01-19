# Generated by Django 4.1.3 on 2023-01-18 12:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("Access", "0010_remove_useraccessmapping_module_identity_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="useraccessmapping",
            name="user_identity",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="user_access",
                to="Access.useridentity",
            ),
        ),
    ]
