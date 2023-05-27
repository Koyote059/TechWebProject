# Generated by Django 4.2.1 on 2023-05-24 19:18

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reservations', '0014_alter_reservation_hour'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='reservation',
            unique_together={('user', 'day', 'hour')},
        ),
    ]
