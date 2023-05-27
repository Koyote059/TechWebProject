# Generated by Django 4.2.1 on 2023-05-25 08:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workout', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='workoutplan',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='workout_plans', to=settings.AUTH_USER_MODEL),
        ),
    ]
