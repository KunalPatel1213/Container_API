from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Booking', '0003_booking_booking_id_booking_cargo_space_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='gowquick_error',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='booking',
            name='gowquick_order_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='booking',
            name='gowquick_response',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='gowquick_status',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AddField(
            model_name='booking',
            name='gowquick_tracking_url',
            field=models.URLField(blank=True, default='', max_length=500),
        ),
    ]
