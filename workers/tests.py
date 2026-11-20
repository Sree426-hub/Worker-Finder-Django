from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.test import Client, TestCase
from django.utils import timezone

from users.models import Register

from .models import Booking, Review, Worker


class SmartBookingTests(TestCase):
    def setUp(self):
        self.worker = Worker.objects.create(
            name='Ravi', skill='plumber', phone='9876501001', address='Main Road, Anantapur',
            aadhaar='234501234001', experience=5)
        self.alice = Register.objects.create(
            name='Alice', email='alice@example.com', password=make_password('pass12345'))
        self.bob = Register.objects.create(
            name='Bob', email='bob@example.com', password=make_password('pass12345'))
        self.day = (timezone.localdate() + timedelta(days=2)).isoformat()

    def customer_client(self, email):
        client = Client()
        client.post('/login/', {'email': email, 'password': 'pass12345'})
        return client

    def worker_client(self):
        client = Client()
        client.post('/worker_login/', {'phone': '9876501001', 'aadhaar': '234501234001'})
        return client

    def book(self, client, slot='morning'):
        return client.post(f'/book/{self.worker.pk}/', {
            'customer_name': 'Alice', 'customer_phone': '9876543210',
            'address': 'Flat 1, Some Road', 'date': self.day, 'time_slot': slot})

    def test_booking_needs_login(self):
        resp = Client().get(f'/book/{self.worker.pk}/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp['Location'])

    def test_double_booking_is_blocked(self):
        alice, bob = self.customer_client('alice@example.com'), self.customer_client('bob@example.com')
        self.book(alice)
        booking = Booking.objects.get()
        self.worker_client().post(f'/update_booking/{booking.pk}/', {'status': 'Accepted'})
        resp = self.book(bob)
        self.assertContains(resp, 'Worker unavailable for this slot')
        self.assertEqual(Booking.objects.count(), 1)
        # a different slot is still free
        self.book(bob, slot='evening')
        self.assertEqual(Booking.objects.count(), 2)

    def test_otp_flow_and_verified_review(self):
        alice = self.customer_client('alice@example.com')
        worker = self.worker_client()
        self.book(alice)
        booking = Booking.objects.get()

        # cannot review before the job is completed
        alice.post(f'/leave_review/{booking.pk}/', {'rating': '5'})
        self.assertEqual(Review.objects.count(), 0)

        worker.post(f'/update_booking/{booking.pk}/', {'status': 'Accepted'})
        booking.refresh_from_db()
        self.assertEqual(len(booking.otp), 4)

        wrong = '0000' if booking.otp != '0000' else '1111'
        worker.post(f'/start_job/{booking.pk}/', {'otp': wrong})
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'Accepted')

        worker.post(f'/start_job/{booking.pk}/', {'otp': booking.otp})
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'Started')

        worker.post(f'/complete_job/{booking.pk}/')
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'Completed')

        # another customer cannot review this booking
        self.customer_client('bob@example.com').post(f'/leave_review/{booking.pk}/', {'rating': '1'})
        self.assertEqual(Review.objects.count(), 0)

        alice.post(f'/leave_review/{booking.pk}/', {'rating': '5', 'comment': 'Great'})
        self.assertEqual(Review.objects.get().rating, 5)

    def test_demo_login(self):
        resp = Client().post('/demo_login/customer/')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], '/my_bookings/')
        resp = Client().post('/demo_login/worker/')
        self.assertEqual(resp['Location'], '/view_bookings/')
        self.assertTrue(Worker.objects.filter(area='Marathahalli', verified=True).exists())
