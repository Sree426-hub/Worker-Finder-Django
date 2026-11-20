import re

from datetime import timedelta

from django import forms
from django.utils import timezone

from .models import Booking, Worker

PHONE_RE = re.compile(r'^[6-9]\d{9}$')
AADHAAR_RE = re.compile(r'^\d{12}$')


def validate_phone(value):
    value = (value or '').strip()
    if not PHONE_RE.match(value):
        raise forms.ValidationError(
            'Enter a valid 10-digit mobile number (starts with 6-9, no spaces or +91).'
        )
    return value


def form_errors(form):
    """Flatten a form's errors into a simple list of strings for templates."""
    return [
        (f"{form.fields[f].label or f.replace('_', ' ').title()}: {e}" if f in form.fields else str(e))
        for f, errs in form.errors.items()
        for e in errs
    ]


class WorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ['name', 'skill', 'phone', 'address', 'area', 'aadhaar', 'experience',
                  'visit_charge', 'day_rate', 'image']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Name is required.')
        return name

    def clean_skill(self):
        skill = self.cleaned_data['skill'].strip()
        if not skill:
            raise forms.ValidationError('Skill is required.')
        return skill

    def clean_phone(self):
        return validate_phone(self.cleaned_data['phone'])

    def clean_address(self):
        address = self.cleaned_data['address'].strip()
        if len(address) < 5:
            raise forms.ValidationError('Enter a complete address.')
        return address

    def clean_aadhaar(self):
        aadhaar = self.cleaned_data['aadhaar'].strip().replace(' ', '')
        if not AADHAAR_RE.match(aadhaar):
            raise forms.ValidationError('Aadhaar must be exactly 12 digits.')
        if Worker.objects.filter(aadhaar=aadhaar).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('A worker with this Aadhaar is already registered.')
        return aadhaar

    def clean_area(self):
        return self.cleaned_data['area'].strip()

    def clean_visit_charge(self):
        return self._check_money(self.cleaned_data['visit_charge'])

    def clean_day_rate(self):
        return self._check_money(self.cleaned_data['day_rate'])

    @staticmethod
    def _check_money(value):
        if value is not None and value > 100000:
            raise forms.ValidationError('Enter an amount up to 100000.')
        return value

    def clean_experience(self):
        exp = self.cleaned_data['experience']
        if exp < 0 or exp > 60:
            raise forms.ValidationError('Experience must be between 0 and 60 years.')
        return exp


class WorkerProfileForm(WorkerForm):
    """Fields a worker may change after login. Aadhaar is not editable."""

    class Meta(WorkerForm.Meta):
        fields = ['name', 'skill', 'phone', 'address', 'area', 'experience',
                  'visit_charge', 'day_rate', 'available', 'available_now', 'image']


class BookingForm(forms.Form):
    customer_name = forms.CharField(max_length=100, label='Name')
    customer_phone = forms.CharField(max_length=15, label='Phone')
    address = forms.CharField(label='Address')
    date = forms.DateField(label='Date')
    time_slot = forms.ChoiceField(choices=Booking.SLOT_CHOICES, label='Time slot')

    def clean(self):
        cleaned = super().clean()
        day, slot = cleaned.get('date'), cleaned.get('time_slot')
        if day and slot:
            today = timezone.localdate()
            if day < today:
                self.add_error('date', 'Pick today or a later date.')
            elif day > today + timedelta(days=30):
                self.add_error('date', 'You can book up to 30 days ahead.')
            elif day == today and timezone.localtime().hour >= Booking.SLOT_END_HOUR[slot]:
                self.add_error('time_slot', 'That slot is already over for today.')
        return cleaned

    def clean_customer_name(self):
        name = self.cleaned_data['customer_name'].strip()
        if not name:
            raise forms.ValidationError('Name is required.')
        return name

    def clean_customer_phone(self):
        return validate_phone(self.cleaned_data['customer_phone'])

    def clean_address(self):
        address = self.cleaned_data['address'].strip()
        if len(address) < 5:
            raise forms.ValidationError('Enter a complete address.')
        return address
