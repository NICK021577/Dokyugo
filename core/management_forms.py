from datetime import timedelta
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify
from .models import Document, ResidentProfile
from .auth import normalize_mobile
import re

class ScheduleForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='From date')
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Through date')
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), initial='08:00', label='First appointment')
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), initial='16:00', label='Finish by')
    interval = forms.TypedChoiceField(choices=[(15, 'Every 15 minutes'), (30, 'Every 30 minutes'), (60, 'Every hour')], coerce=int, initial=30, label='Appointment interval')
    capacity = forms.IntegerField(min_value=1, max_value=50, initial=5, label='Places per time slot')
    weekdays_only = forms.BooleanField(initial=True, required=False, label='Weekdays only (Monday–Friday)')
    def clean(self):
        data = super().clean()
        start, end = data.get('start_date'), data.get('end_date')
        if start and start < timezone.localdate():
            self.add_error('start_date', 'Choose today or a future date.')
        if start and end and (end < start or end-start > timedelta(days=61)):
            self.add_error('end_date', 'Choose a range of up to 62 days ending on or after the first date.')
        if end and end > timezone.localdate()+timedelta(days=365):
            self.add_error('end_date', 'Publish availability within the next year.')
        if data.get('start_time') and data.get('end_time') and data['end_time'] <= data['start_time']:
            self.add_error('end_time', 'The finish time must be after the first appointment.')
        return data

class DocumentEditorForm(forms.ModelForm):
    requirements_text = forms.CharField(label='Requirements', widget=forms.Textarea(attrs={'rows': 6}), help_text='One requirement per line. These appear immediately on the resident document page.')
    requirements_verified = forms.BooleanField(required=False, label='These requirements have been confirmed by barangay staff')
    class Meta:
        model = Document
        fields = ['name', 'group', 'description', 'fee', 'processing_time', 'bookable']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            reqs = list(self.instance.requirements.all())
            self.fields['requirements_text'].initial = '\n'.join(r.text for r in reqs)
            self.fields['requirements_verified'].initial = bool(reqs) and all(r.confirmed for r in reqs)
    def clean_name(self):
        name = self.cleaned_data['name']
        if not self.instance.pk and Document.objects.filter(slug=slugify(name)).exists():
            raise ValidationError('A document with this name already exists.')
        if not slugify(name):
            raise ValidationError('Enter a document name containing letters or numbers.')
        return name
    def clean_requirements_text(self):
        lines = [line.strip() for line in self.cleaned_data['requirements_text'].splitlines() if line.strip()]
        if not lines or len(lines) > 30 or any(len(line) > 250 for line in lines):
            raise ValidationError('Enter 1–30 requirements, with up to 250 characters per line.')
        return lines

class AccountAccessForm(forms.Form):
    role = forms.ChoiceField(choices=[('resident', 'Resident'), ('staff', 'Staff')])
    active = forms.BooleanField(required=False, label='Account active')

class AccountEditorForm(forms.Form):
    first_name = forms.CharField(max_length=150, label='First name')
    last_name = forms.CharField(max_length=150, label='Last name')
    middle_name = forms.CharField(max_length=100, required=False, label='Middle name')
    email = forms.EmailField(max_length=150, label='Email / login', help_text='Use this email or the mobile number to log in after saving.')
    mobile = forms.CharField(max_length=30, required=False, label='Mobile number', widget=forms.TextInput(attrs={'type':'tel','autocomplete':'tel'}))
    address = forms.CharField(max_length=250, required=False, label='Residential address')
    role = forms.ChoiceField(choices=[('resident','Resident'),('staff','Staff')])
    active = forms.BooleanField(required=False, label='Allow sign-in')
    new_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'autocomplete':'new-password'}), help_text='Leave both password fields empty to keep the current password.', label='New password')
    confirm_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'autocomplete':'new-password'}), label='Confirm new password')

    def __init__(self, *args, user, **kwargs):
        self.user = user
        self.profile = ResidentProfile.objects.filter(user=user).first()
        initial = {'first_name':user.first_name, 'last_name':user.last_name, 'email':user.email,
                   'role':'staff' if user.is_staff else 'resident', 'active':user.is_active}
        if self.profile:
            initial.update(middle_name=self.profile.middle_name, mobile=self.profile.mobile, address=self.profile.address)
        if user.is_superuser:
            initial['role'] = 'admin'
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)
        if user.is_superuser:
            self.fields['role'].choices = [('admin','Administrator')]
            self.fields['role'].disabled = self.fields['active'].disabled = True
            self.fields['role'].help_text = 'Administrator access is protected on this page.'
    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if get_user_model().objects.exclude(pk=self.user.pk).filter(Q(username__iexact=email)|Q(email__iexact=email)).exists():
            raise ValidationError('Another account already uses this email or login.')
        return email
    def clean_mobile(self):
        mobile = normalize_mobile(self.cleaned_data['mobile'])
        if not mobile:
            if self.profile:
                raise ValidationError('Enter a mobile number for this existing profile.')
            return ''
        if not re.fullmatch(r'09\d{9}', mobile):
            raise ValidationError('Enter an 11-digit Philippine mobile number starting with 09.')
        if ResidentProfile.objects.exclude(user=self.user).filter(mobile=mobile).exists():
            raise ValidationError('Another account already uses this mobile number.')
        return mobile
    def clean(self):
        data = super().clean()
        if not self.profile and not data.get('mobile') and (data.get('middle_name') or data.get('address')):
            self.add_error('mobile','Add a mobile number to save the profile details.')
        password = data.get('new_password','')
        if password != data.get('confirm_password',''):
            self.add_error('confirm_password','The passwords do not match.')
        if password:
            candidate = get_user_model()(username=data.get('email',''), email=data.get('email',''), first_name=data.get('first_name',''), last_name=data.get('last_name',''))
            try:
                validate_password(password,candidate)
            except ValidationError as exc:
                self.add_error('new_password',exc)
        return data

class AccountDeletionForm(forms.Form):
    mode = forms.ChoiceField(choices=[('archive','Delete account and keep its history'),('permanent','Permanently delete an unused account')], initial='archive', label='Deletion method')
    confirmation = forms.CharField(label='Type the account email or login to confirm')
    acknowledge = forms.BooleanField(label='I understand that sign-in will be removed and pending bookings will be cancelled.')
    def __init__(self, *args, user, can_purge, **kwargs):
        self.user, self.can_purge = user, can_purge
        super().__init__(*args, **kwargs)
        if not can_purge:
            self.fields['mode'].choices = [('archive','Delete account and keep its history')]
    def clean_confirmation(self):
        value = self.cleaned_data['confirmation'].strip()
        expected = self.user.email or self.user.username
        if value.casefold() != expected.casefold():
            raise ValidationError('The confirmation does not match this account.')
        return value
