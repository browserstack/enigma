# Generated by Django 4.1.3 on 2022-12-19 10:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AccessV2",
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
                ("access_label", models.JSONField(default=dict)),
                ("is_auto_approved", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="gitAcces",
            fields=[
                ("requested_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                ("requestInfo", models.JSONField(default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Pending", "pending"),
                            ("Approved", "approved"),
                            ("Declined", "declined"),
                            ("Processing", "processing"),
                            ("Revoked", "revoked"),
                        ],
                        default="Pending",
                        max_length=255,
                    ),
                ),
                ("requestDateUTC", models.CharField(max_length=255)),
                (
                    "RevokeDateUTC",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "requestId",
                    models.CharField(max_length=255, primary_key=True, serialize=False),
                ),
                ("approver", models.CharField(blank=True, max_length=255)),
                ("requester", models.CharField(max_length=255)),
                ("reason", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="GroupV2",
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
                ("group_id", models.CharField(max_length=255, unique=True)),
                ("requested_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=128)),
                ("description", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Pending", "pending"),
                            ("Approved", "approved"),
                            ("Declined", "declined"),
                            ("Deprecated", "deprecated"),
                        ],
                        default="Pending",
                        max_length=255,
                    ),
                ),
                ("decline_reason", models.TextField(blank=True, null=True)),
                ("needsAccessApprove", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Permission",
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
                ("label", models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Role",
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
                ("label", models.CharField(max_length=255, unique=True)),
                ("permission", models.ManyToManyField(to="Access.permission")),
            ],
        ),
        migrations.CreateModel(
            name="SshPublicKey",
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
                ("key", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[("Active", "active"), ("Revoked", "revoked")],
                        default="Active",
                        max_length=100,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="User",
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
                (
                    "gitusername",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("name", models.CharField(max_length=255, null=True)),
                ("email", models.EmailField(max_length=254, null=True)),
                ("phone", models.IntegerField(blank=True, null=True)),
                ("is_bot", models.BooleanField(default=False)),
                (
                    "bot_type",
                    models.CharField(
                        choices=[("None", "none"), ("Github", "github")],
                        default="None",
                        max_length=100,
                    ),
                ),
                ("alerts_enabled", models.BooleanField(default=False)),
                ("is_manager", models.BooleanField(default=False)),
                ("is_ops", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("ssh_pub_key", models.TextField(blank=True, null=True)),
                ("avatar", models.TextField(blank=True, null=True)),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("1", "active"),
                            ("2", "offboarding"),
                            ("3", "offboarded"),
                        ],
                        default=1,
                        max_length=255,
                    ),
                ),
                ("offbaord_date", models.DateTimeField(blank=True, null=True)),
                (
                    "revoker",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="user_revoker",
                        to="Access.user",
                    ),
                ),
                ("role", models.ManyToManyField(blank=True, to="Access.role")),
                (
                    "ssh_public_key",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="user",
                        to="Access.sshpublickey",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserAccessMapping",
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
                ("request_id", models.CharField(max_length=255, unique=True)),
                ("requested_on", models.DateTimeField(auto_now_add=True)),
                ("approved_on", models.DateTimeField(blank=True, null=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                ("request_reason", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Pending", "pending"),
                            ("SecondaryPending", "secondarypending"),
                            ("Processing", "processing"),
                            ("Approved", "approved"),
                            ("GrantFailed", "grantfailed"),
                            ("Declined", "declined"),
                            ("Offboarding", "offboarding"),
                            ("ProcessingRevoke", "processingrevoke"),
                            ("RevokeFailed", "revokefailed"),
                            ("Revoked", "revoked"),
                        ],
                        default="Pending",
                        max_length=100,
                    ),
                ),
                ("decline_reason", models.TextField(blank=True, null=True)),
                (
                    "access_type",
                    models.CharField(
                        choices=[("Individual", "individual"), ("Group", "group")],
                        default="Individual",
                        max_length=255,
                    ),
                ),
                (
                    "access",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="Access.accessv2",
                    ),
                ),
                (
                    "approver_1",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="approver_1",
                        to="Access.user",
                    ),
                ),
                (
                    "approver_2",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="approver_2",
                        to="Access.user",
                    ),
                ),
                (
                    "revoker",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="user_access_revoker",
                        to="Access.user",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="Access.user"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MembershipV2",
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
                ("membership_id", models.CharField(max_length=255, unique=True)),
                ("is_owner", models.BooleanField(default=False)),
                ("requested_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Pending", "pending"),
                            ("Approved", "approved"),
                            ("Declined", "declined"),
                            ("Revoked", "revoked"),
                        ],
                        default="Pending",
                        max_length=255,
                    ),
                ),
                ("reason", models.TextField(blank=True, null=True)),
                ("decline_reason", models.TextField(blank=True, null=True)),
                (
                    "approver",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="membership_approver",
                        to="Access.user",
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="membership_group",
                        to="Access.groupv2",
                    ),
                ),
                (
                    "requested_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="membership_requester",
                        to="Access.user",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="membership_user",
                        to="Access.user",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="groupv2",
            name="approver",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="group_approver",
                to="Access.user",
            ),
        ),
        migrations.AddField(
            model_name="groupv2",
            name="requester",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="group_requester",
                to="Access.user",
            ),
        ),
        migrations.CreateModel(
            name="GroupAccessMapping",
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
                ("request_id", models.CharField(max_length=255, unique=True)),
                ("requested_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                ("request_reason", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Pending", "pending"),
                            ("SecondaryPending", "secondarypending"),
                            ("Approved", "approved"),
                            ("Declined", "declined"),
                            ("Revoked", "revoked"),
                            ("Inactive", "inactive"),
                        ],
                        default="Pending",
                        max_length=100,
                    ),
                ),
                ("decline_reason", models.TextField(blank=True, null=True)),
                (
                    "access",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="Access.accessv2",
                    ),
                ),
                (
                    "approver_1",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="g_approver_1",
                        to="Access.user",
                    ),
                ),
                (
                    "approver_2",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="g_approver_2",
                        to="Access.user",
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="Access.groupv2"
                    ),
                ),
                (
                    "requested_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="g_requester",
                        to="Access.user",
                    ),
                ),
                (
                    "revoker",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="group_access_revoker",
                        to="Access.user",
                    ),
                ),
            ],
        ),
    ]
