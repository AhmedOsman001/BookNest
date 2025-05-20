from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('actor_object_id', models.CharField(blank=True, max_length=255, null=True)),
                ('verb', models.CharField(max_length=255)),
                ('target_object_id', models.CharField(blank=True, max_length=255, null=True)),
                ('action_object_id', models.CharField(blank=True, max_length=255, null=True)),
                ('data', models.JSONField(blank=True, default=dict)),
                ('read', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('action_object_content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='action_object_notifications', to='contenttypes.contenttype')),
                ('actor_content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='actor_notifications', to='contenttypes.contenttype')),
                ('notification_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='notifications.notificationtype')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
                ('target_content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='target_notifications', to='contenttypes.contenttype')),
            ],
            options={
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['recipient'], name='notif_recipient_idx'), models.Index(fields=['read'], name='notif_read_idx')],
            },
        ),
    ]