# Generated by Django 4.2.7 on 2023-12-16 16:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("uzivatel", "0007_usernotificationtype_text_cs_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="usernotificationtype",
            options={
                "verbose_name": "uzivatel.models.UserNotificationType.name",
                "verbose_name_plural": "uzivatel.models.UserNotificationType.namePlural",
            },
        ),
        migrations.AlterField(
            model_name="notificationslog",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="notification_log_items",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
