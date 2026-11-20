from django.conf import settings
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from users.models import Register
from workers.demo import ensure_demo_data


def home(request):
    return render(request, 'home.html')


def registration(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        errors = []
        if not name:
            errors.append('Name is required.')
        try:
            validate_email(email)
        except ValidationError:
            errors.append('Enter a valid email address.')
        else:
            if Register.objects.filter(email__iexact=email).exists():
                errors.append('This email is already registered.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')

        if errors:
            return render(request, 'registration.html',
                          {'errors': errors, 'data': request.POST})

        Register.objects.create(
            name=name,
            email=email,
            password=make_password(password),  # never store plain text
        )
        messages.success(request, 'Registration successful. Please login.')
        return redirect('/login/')

    return render(request, 'registration.html')


def _safe_next(request):
    """Where to go after login. Only local paths are allowed."""
    target = request.POST.get('next') or request.GET.get('next') or ''
    ok = url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure())
    return target if ok and target.startswith('/') else ''


def login(request):
    next_url = _safe_next(request)

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        user = Register.objects.filter(email__iexact=email).first()

        if user and check_password(password, user.password):
            request.session.cycle_key()
            request.session['user_id'] = user.id
            request.session['user_name'] = user.name
            return redirect(next_url or '/home/')

        messages.error(request, 'Invalid Email or Password')

    return render(request, 'login.html',
                  {'next': next_url, 'demo_enabled': settings.DEMO_LOGIN_ENABLED})


def logout(request):
    request.session.flush()
    return redirect('/home/')


@require_POST
def demo_login(request, role):
    """1-click login with pre-loaded Bengaluru demo data (for recruiters and demos)."""
    if not settings.DEMO_LOGIN_ENABLED or role not in ('customer', 'worker'):
        raise Http404
    customer, worker = ensure_demo_data()
    request.session.flush()
    if role == 'customer':
        request.session['user_id'] = customer.id
        request.session['user_name'] = customer.name
        return redirect('/my_bookings/')
    request.session['worker_id'] = worker.id
    return redirect('/view_bookings/')
