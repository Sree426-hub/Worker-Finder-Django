"""Realistic Bengaluru demo data for the 1-click demo logins."""
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils import timezone

from users.models import Register

from .models import Booking, Review, Worker

DEMO_CUSTOMER_EMAIL = 'demo.customer@workerfinder.test'
DEMO_WORKER_AADHAAR = '999000000001'  # Ravi Kumar, the demo worker account

DEMO_WORKERS = [
    dict(name='Ravi Kumar', skill='plumber', phone='9845011001', area='Marathahalli',
         address='14, Kundalahalli Gate, Marathahalli, Bengaluru 560037', aadhaar=DEMO_WORKER_AADHAAR,
         experience=6, visit_charge=199, day_rate=900, verified=True, available_now=True),
    dict(name='Suresh Gowda', skill='electrician', phone='9845011002', area='Whitefield',
         address='Hope Farm Junction, Whitefield, Bengaluru 560066', aadhaar='999000000002',
         experience=8, visit_charge=249, day_rate=1000, verified=True, available_now=True),
    dict(name='Mahesh Naik', skill='carpenter', phone='9845011003', area='HSR Layout',
         address='27th Main, Sector 2, HSR Layout, Bengaluru 560102', aadhaar='999000000003',
         experience=10, visit_charge=299, day_rate=1200, verified=True, available_now=False),
    dict(name='Imran Khan', skill='AC technician', phone='9845011004', area='Marathahalli',
         address='Outer Ring Road, Marathahalli, Bengaluru 560037', aadhaar='999000000004',
         experience=5, visit_charge=349, day_rate=1100, verified=False, available_now=True),
    dict(name='Lakshmi Devi', skill='painter', phone='9845011005', area='Whitefield',
         address='ITPL Main Road, Whitefield, Bengaluru 560066', aadhaar='999000000005',
         experience=4, visit_charge=None, day_rate=950, verified=False, available_now=False),
    dict(name='Venkatesh', skill='mechanic', phone='9845011006', area='HSR Layout',
         address='19th Main, HSR Layout, Bengaluru 560102', aadhaar='999000000006',
         experience=7, visit_charge=199, day_rate=1000, verified=True, available_now=True),
]


@transaction.atomic
def ensure_demo_data():
    """Create the demo customer, workers, bookings and a review (only what is missing)."""
    customer = Register.objects.filter(email=DEMO_CUSTOMER_EMAIL).first()
    if customer is None:
        customer = Register.objects.create(
            name='Demo Customer', email=DEMO_CUSTOMER_EMAIL,
            password=make_password(None),  # unusable: demo accounts log in by button only
        )

    workers = {}
    for data in DEMO_WORKERS:
        worker = Worker.objects.filter(aadhaar=data['aadhaar']).first()
        if worker is None:
            worker = Worker.objects.create(available=True, **data)
        workers[data['aadhaar']] = worker

    if not Booking.objects.filter(customer=customer).exists():
        today = timezone.localdate()
        ravi = workers[DEMO_WORKER_AADHAAR]
        suresh = workers['999000000002']
        base = dict(customer=customer, customer_name='Demo Customer', phone='9900112233',
                    address='Flat 302, Prestige Tower, Marathahalli, Bengaluru 560037')
        done = Booking.objects.create(
            worker=ravi, date=today - timedelta(days=3), time_slot='morning',
            status='Completed', otp='4821', **base)
        Review.objects.create(booking=done, worker=ravi, customer=customer, rating=5,
                              comment='Fixed the kitchen leak in under an hour. Arrived on time.')
        Booking.objects.create(worker=suresh, date=today + timedelta(days=1), time_slot='afternoon',
                               status='Accepted', otp='7305', **base)
        Booking.objects.create(worker=ravi, date=today + timedelta(days=1), time_slot='morning',
                               status='Pending', **base)

    return customer, workers[DEMO_WORKER_AADHAAR]
