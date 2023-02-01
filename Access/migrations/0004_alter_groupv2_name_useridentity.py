# Generated by Django 4.1.3 on 2023-01-14 05:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("Access", "0003_user_is_manager_user_is_ops"),
    ]

    operations = [
        migrations.AlterField(
            model_name="groupv2",
            name="name",
            field=models.CharField(max_length=128, unique=True),
        ),
        migrations.CreateModel(
            name="UserIdentity",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("access_tag", models.CharField(max_length=255)),
                ("identity", models.JSONField(default=dict)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="user_module_identity",
                        to="Access.user",
                    ),
                ),
            ],
        ),
    ]
