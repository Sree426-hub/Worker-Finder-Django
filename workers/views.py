import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from users.models import Register

from .forms import BookingForm, WorkerForm, WorkerProfileForm, form_errors
from .models import Booking, Review, Worker

MAX_OTP_ATTEMPTS = 5


# ---------- helpers ----------

def _customer(request):
    user_id = request.session.get('user_id')
    return Register.objects.filter(pk=user_id).first() if user_id else None


def _worker(request):
    worker_id = request.session.get('worker_id')
    return Worker.objects.filter(pk=worker_id).first() if worker_id else None


def _rated_workers():
    return Worker.objects.annotate(
        avg_rating=Avg('reviews__rating'), review_count=Count('reviews')
    )


# ---------- worker registration / public pages ----------

def worker_register(request):
    if request.method == 'POST':
        form = WorkerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Worker registered successfully.')
            return redirect('/home/')
        return render(request, 'worker_register.html',
                      {'errors': form_errors(form), 'data': request.POST})

    return render(request, 'worker_register.html')


def workers_list(request):
    search = request.GET.get('search', '').strip()
    area = request.GET.get('area', '').strip()
    urgent = request.GET.get('urgent') == '1'

    workers = _rated_workers()
    if search:
        workers = workers.filter(skill__icontains=search)
    if area:
        workers = workers.filter(area__icontains=area)
    if urgent:  # same-day help: accepting bookings AND free right now
        workers = workers.filter(available=True, available_now=True)
    workers = workers.order_by('-available', '-available_now', '-verified', '-avg_rating', 'name')

    areas = (Worker.objects.exclude(area='').values_list('area', flat=True)
             .distinct().order_by('area'))
    return render(request, 'workers_list.html', {
        'workers': workers, 'search': search, 'area': area, 'urgent': urgent, 'areas': areas,
    })


def worker_detail(request, pk):
    worker = get_object_or_404(_rated_workers(), pk=pk)
    reviews = worker.reviews.select_related('customer').order_by('-created_at')
    return render(request, 'worker_detail.html', {'worker': worker, 'reviews': reviews})


# ---------- customer side ----------

def book_worker(request, pk):
    worker = get_object_or_404(Worker, pk=pk)

    customer = _customer(request)
    if customer is None:
        messages.info(request, 'Please login to book a worker.')
        return redirect(f'/login/?next=/book/{pk}/')

    if not worker.available:
        messages.error(request, f'{worker.name} is currently not available.')
        return redirect('/workers/')

    today = timezone.localdate()
    context = {
        'worker': worker,
        'today': today.isoformat(),
        'max_date': (today + timedelta(days=30)).isoformat(),
        'slots': Booking.SLOT_CHOICES,
    }

    if request.method == 'POST':
        form = BookingForm(request.POST)
        errors = []
        if form.is_valid():
            cd = form.cleaned_data
            if Booking.slot_taken(worker, cd['date'], cd['time_slot']):
                errors = ['Worker unavailable for this slot, please pick another time.']
            elif Booking.objects.filter(
                    customer=customer, worker=worker, date=cd['date'],
                    time_slot=cd['time_slot'], status__in=('Pending', 'Accepted')).exists():
                errors = ['You already requested this worker for this slot.']
            else:
                Booking.objects.create(
                    worker=worker, customer=customer,
                    customer_name=cd['customer_name'], phone=cd['customer_phone'],
                    address=cd['address'], date=cd['date'], time_slot=cd['time_slot'],
                )
                messages.success(
                    request,
                    f'Booking sent to {worker.name}. You will see a 4-digit start code here '
                    f'once the worker accepts.')
                return redirect('/my_bookings/')
        else:
            errors = form_errors(form)
        return render(request, 'book_worker.html',
                      {**context, 'errors': errors, 'data': request.POST})

    return render(request, 'book_worker.html',
                  {**context, 'data': {'customer_name': customer.name}})


def my_bookings(request):
    customer = _customer(request)
    if customer is None:
        messages.info(request, 'Please login to see your bookings.')
        return redirect('/login/?next=/my_bookings/')

    bookings = (Booking.objects.filter(customer=customer)
                .select_related('worker', 'review').order_by('-id'))
    return render(request, 'my_bookings.html', {'bookings': bookings, 'customer': customer})


@require_POST
def cancel_booking(request, pk):
    customer = _customer(request)
    if customer is None:
        return redirect('/login/?next=/my_bookings/')
    booking = get_object_or_404(Booking, pk=pk, customer=customer)
    if booking.status in ('Pending', 'Accepted'):
        booking.status = 'Cancelled'
        booking.save(update_fields=['status'])
        messages.success(request, 'Booking cancelled.')
    else:
        messages.error(request, 'This booking can no longer be cancelled.')
    return redirect('/my_bookings/')


@require_POST
def leave_review(request, pk):
    customer = _customer(request)
    if customer is None:
        return redirect('/login/?next=/my_bookings/')
    booking = get_object_or_404(Booking, pk=pk, customer=customer)

    if booking.status != 'Completed':
        messages.error(request, 'You can review a worker only after the job is completed.')
    elif Review.objects.filter(booking=booking).exists():
        messages.error(request, 'You already reviewed this booking.')
    else:
        try:
            rating = int(request.POST.get('rating', ''))
        except ValueError:
            rating = 0
        if 1 <= rating <= 5:
            Review.objects.create(
                booking=booking, worker=booking.worker, customer=customer, rating=rating,
                comment=request.POST.get('comment', '').strip()[:500],
            )
            messages.success(request, 'Thanks for your review!')
        else:
            messages.error(request, 'Choose a rating from 1 to 5.')
    return redirect('/my_bookings/')


# ---------- worker side ----------

def worker_login(request):
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        aadhaar = request.POST.get('aadhaar', '').strip()

        worker = Worker.objects.filter(phone=phone, aadhaar=aadhaar).first()

        if worker:
            request.session.cycle_key()
            request.session['worker_id'] = worker.id
            return redirect('/view_bookings/')

        return render(request, 'worker_login.html',
                      {'error': 'Invalid phone number or Aadhaar',
                       'demo_enabled': settings.DEMO_LOGIN_ENABLED})

    return render(request, 'worker_login.html', {'demo_enabled': settings.DEMO_LOGIN_ENABLED})


def view_bookings(request):
    worker_id = request.session.get('worker_id')

    if not worker_id:
        return redirect('/worker_login/')

    worker = Worker.objects.filter(pk=worker_id).first()
    if worker is None:  # worker was deleted while logged in
        request.session.flush()
        return redirect('/worker_login/')

    bookings = (Booking.objects.filter(worker=worker)
                .select_related('customer').order_by('-id'))

    return render(request, 'view_bookings.html', {
        'bookings': bookings, 'worker': worker, 'max_attempts': MAX_OTP_ATTEMPTS,
    })


def edit_profile(request):
    worker = _worker(request)
    if worker is None:
        return redirect('/worker_login/')
    worker_id = worker.pk

    # values shown in the form (taken before the form touches the instance)
    values = {
        'name': worker.name, 'skill': worker.skill, 'phone': worker.phone,
        'address': worker.address, 'area': worker.area, 'experience': worker.experience,
        'visit_charge': worker.visit_charge, 'day_rate': worker.day_rate,
        'available': worker.available, 'available_now': worker.available_now,
    }

    if request.method == 'POST':
        form = WorkerProfileForm(request.POST, request.FILES, instance=worker)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('/view_bookings/')
        values = request.POST.dict()
        values['available'] = 'available' in request.POST
        values['available_now'] = 'available_now' in request.POST
        return render(request, 'edit_profile.html',
                      {'worker': Worker.objects.get(pk=worker_id), 'data': values,
                       'errors': form_errors(form)})

    return render(request, 'edit_profile.html', {'worker': worker, 'data': values})


@require_POST
def toggle_available_now(request):
    worker = _worker(request)
    if worker is None:
        return redirect('/worker_login/')
    worker.available_now = not worker.available_now
    worker.save(update_fields=['available_now'])
    if worker.available_now:
        messages.success(request, 'You are now shown as Available Now for same-day jobs.')
    else:
        messages.success(request, 'Available Now is off.')
    return redirect('/view_bookings/')


@require_POST
def update_booking(request, pk):
    """Worker accepts or rejects a pending booking."""
    worker = _worker(request)
    if worker is None:
        return redirect('/worker_login/')

    booking = get_object_or_404(Booking, pk=pk, worker=worker)
    status = request.POST.get('status')
    if booking.status != 'Pending' or status not in ('Accepted', 'Rejected'):
        return redirect('/view_bookings/')

    if status == 'Rejected':
        booking.status = 'Rejected'
        booking.save(update_fields=['status'])
        return redirect('/view_bookings/')

    with transaction.atomic():
        # re-check at accept time so two customers cannot both get the same slot
        if booking.date and Booking.slot_taken(worker, booking.date, booking.time_slot,
                                               exclude_pk=booking.pk):
            messages.error(request, 'You already have a confirmed job in this slot.')
            return redirect('/view_bookings/')

        booking.status = 'Accepted'
        booking.otp = f'{secrets.randbelow(10000):04d}'
        booking.otp_attempts = 0
        booking.save(update_fields=['status', 'otp', 'otp_attempts'])

        if booking.date:  # other requests for the same slot can no longer be served
            Booking.objects.filter(
                worker=worker, date=booking.date, time_slot=booking.time_slot, status='Pending'
            ).exclude(pk=booking.pk).update(status='Rejected')

    messages.success(request, 'Booking accepted. The customer can now see the start code.')
    return redirect('/view_bookings/')


@require_POST
def start_job(request, pk):
    """Worker enters the customer's 4-digit code to start the job."""
    worker = _worker(request)
    if worker is None:
        return redirect('/worker_login/')

    booking = get_object_or_404(Booking, pk=pk, worker=worker)
    if booking.status != 'Accepted':
        return redirect('/view_bookings/')

    if booking.otp_attempts >= MAX_OTP_ATTEMPTS:
        messages.error(request, 'Too many wrong codes. Ask the customer to cancel and rebook.')
        return redirect('/view_bookings/')

    entered = request.POST.get('otp', '').strip()
    if len(entered) == 4 and secrets.compare_digest(entered.encode(), booking.otp.encode()):
        booking.status = 'Started'
        booking.save(update_fields=['status'])
        messages.success(request, 'Code correct. Job started.')
    else:
        booking.otp_attempts += 1
        booking.save(update_fields=['otp_attempts'])
        left = MAX_OTP_ATTEMPTS - booking.otp_attempts
        messages.error(request, f'Wrong code. {left} attempt(s) left.')
    return redirect('/view_bookings/')


@require_POST
def complete_job(request, pk):
    worker = _worker(request)
    if worker is None:
        return redirect('/worker_login/')

    booking = get_object_or_404(Booking, pk=pk, worker=worker)
    # old bookings made before customer accounts existed have no code to enter
    legacy = booking.customer_id is None and booking.status == 'Accepted'
    if booking.status == 'Started' or legacy:
        booking.status = 'Completed'
        booking.save(update_fields=['status'])
        messages.success(request, 'Job marked as completed.')
    return redirect('/view_bookings/')
