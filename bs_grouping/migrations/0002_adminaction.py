# Generated by Django 5.2.3 on 2025-07-11 12:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bs_grouping", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AdminAction",
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
                    "action_type",
                    models.CharField(
                        choices=[
                            ("member_create", "Member Created"),
                            ("member_edit", "Member Edited"),
                            ("member_delete", "Member Deleted"),
                            ("group_create", "Group Created"),
                            ("group_edit", "Group Edited"),
                            ("group_delete", "Group Deleted"),
                            ("member_assign", "Member Assigned to Group"),
                            ("member_remove", "Member Removed from Group"),
                            ("leader_assign", "Leader Assigned"),
                            ("leader_remove", "Leader Removed"),
                            ("grouping_run", "Automatic Grouping Run"),
                            ("impersonate", "Admin Impersonated Member"),
                        ],
                        max_length=20,
                    ),
                ),
                ("description", models.TextField()),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                (
                    "admin_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="performed_admin_actions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "target_group",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="admin_actions",
                        to="bs_grouping.group",
                    ),
                ),
                (
                    "target_member",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="received_admin_actions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-timestamp"],
            },
        ),
    ]
