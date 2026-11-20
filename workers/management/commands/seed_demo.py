from django.core.management.base import BaseCommand

from workers.demo import ensure_demo_data


class Command(BaseCommand):
    help = 'Create the demo customer, Bengaluru demo workers and sample bookings.'

    def handle(self, *args, **options):
        ensure_demo_data()
        self.stdout.write(self.style.SUCCESS('Demo data is ready.'))
