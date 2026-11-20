from urllib.parse import quote

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Worker(models.Model):
    name = models.CharField(max_length=100)
    skill = models.CharField(max_length=100)
    phone = models.CharField(max_length=10)
    address = models.TextField()
    # Area / locality used for local search (e.g. Marathahalli, Whitefield)
    area = models.CharField(max_length=100, blank=True, default='')
    aadhaar = models.CharField(max_length=12)
    experience = models.IntegerField()
    # Rate card (rupees)
    visit_charge = models.PositiveIntegerField(null=True, blank=True)
    day_rate = models.PositiveIntegerField(null=True, blank=True)
    # available = takes bookings at all; available_now = can come today / urgent
    available = models.BooleanField(default=True)
    available_now = models.BooleanField(default=False)
    # Only an admin can set this, after checking the worker's ID
    verified = models.BooleanField(default=False)
    image = models.ImageField(upload_to='workers/', null=True, blank=True)

    def __str__(self):
        return self.name


def whatsapp_url(phone, text):
    """Click-to-chat link. A 10 digit Indian number gets the 91 prefix."""
    digits = ''.join(ch for ch in (phone or '') if ch.isdigit())
    if len(digits) == 10:
        digits = '91' + digits
    return f'https://wa.me/{digits}?text={quote(text)}'


class Booking(models.Model):
    SLOT_CHOICES = (
        ('morning', 'Morning (8 AM - 12 PM)'),
        ('afternoon', 'Afternoon (12 PM - 4 PM)'),
        ('evening', 'Evening (4 PM - 8 PM)'),
    )
    SLOT_END_HOUR = {'morning': 12, 'afternoon': 16, 'evening': 20}

    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
        ('Started', 'Started'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    # A slot is taken once a worker has accepted (or started) a job in it
    BLOCKING_STATUSES = ('Accepted', 'Started')

    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    customer = models.ForeignKey(
        'users.Register', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='bookings',
    )
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    date = models.DateField(null=True, blank=True)
    time_slot = models.CharField(max_length=10, choices=SLOT_CHOICES, blank=True, default='')

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )
    # 4-digit code the customer tells the worker to start the job
    otp = models.CharField(max_length=4, blank=True, default='')
    otp_attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return f'{self.customer_name} -> {self.worker.name} ({self.status})'

    @classmethod
    def slot_taken(cls, worker, date, slot, exclude_pk=None):
        qs = cls.objects.filter(
            worker=worker, date=date, time_slot=slot,
            status__in=cls.BLOCKING_STATUSES,
        )
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        return qs.exists()

    @property
    def status_color(self):
        return {
            'Pending': 'warning', 'Accepted': 'primary', 'Started': 'info',
            'Completed': 'success', 'Rejected': 'danger', 'Cancelled': 'secondary',
        }.get(self.status, 'secondary')

    def _when(self):
        if not self.date:
            return ''
        return f'{self.date:%d %b %Y}, {self.get_time_slot_display()}'

    @property
    def whatsapp_worker_url(self):
        """Customer -> worker message after booking."""
        text = (
            f'Hi {self.worker.name}, I booked you on Worker Finder for {self._when()}. '
            f'Name: {self.customer_name}. Address: {self.address}'
        )
        return whatsapp_url(self.worker.phone, text)

    @property
    def whatsapp_customer_url(self):
        """Worker -> customer message. Never contains the OTP."""
        text = (
            f'Hi {self.customer_name}, this is {self.worker.name} from Worker Finder. '
            f'I have accepted your booking for {self._when()}. '
            f'Please keep your 4-digit start code ready when I arrive.'
        )
        return whatsapp_url(self.phone, text)


class Review(models.Model):
    # One review per completed booking, so only real customers can review
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey('users.Register', on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return f'{self.worker.name}: {self.rating}/5'
