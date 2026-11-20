import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

SLOT_CHOICES = [
    ('morning', 'Morning (8 AM - 12 PM)'),
    ('afternoon', 'Afternoon (12 PM - 4 PM)'),
    ('evening', 'Evening (4 PM - 8 PM)'),
]
STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Accepted', 'Accepted'),
    ('Rejected', 'Rejected'),
    ('Started', 'Started'),
    ('Completed', 'Completed'),
    ('Cancelled', 'Cancelled'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_hash_passwords'),
        ('workers', '0004_remove_booking_booking_date_and_more'),
    ]

    operations = [
        migrations.AddField(model_name='worker', name='area',
                            field=models.CharField(blank=True, default='', max_length=100)),
        migrations.AddField(model_name='worker', name='visit_charge',
                            field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField(model_name='worker', name='day_rate',
                            field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField(model_name='worker', name='available_now',
                            field=models.BooleanField(default=False)),
        migrations.AddField(model_name='worker', name='verified',
                            field=models.BooleanField(default=False)),
        migrations.AddField(model_name='booking', name='customer',
                            field=models.ForeignKey(blank=True, null=True,
                                                    on_delete=django.db.models.deletion.SET_NULL,
                                                    related_name='bookings', to='users.register')),
        migrations.AddField(model_name='booking', name='date',
                            field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name='booking', name='time_slot',
                            field=models.CharField(blank=True, choices=SLOT_CHOICES, default='', max_length=10)),
        migrations.AddField(model_name='booking', name='otp',
                            field=models.CharField(blank=True, default='', max_length=4)),
        migrations.AddField(model_name='booking', name='otp_attempts',
                            field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name='booking', name='created_at',
                            field=models.DateTimeField(default=django.utils.timezone.now, editable=False)),
        migrations.AlterField(model_name='booking', name='status',
                              field=models.CharField(choices=STATUS_CHOICES, default='Pending', max_length=20)),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(5)])),
                ('comment', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('booking', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                                 related_name='review', to='workers.booking')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                               related_name='reviews', to='users.register')),
                ('worker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name='reviews', to='workers.worker')),
            ],
        ),
    ]
