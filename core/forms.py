import re
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, F
from django.utils import timezone
from .auth import normalize_mobile
from .models import AppointmentSlot, Document, ResidentProfile

class RegistrationForm(forms.Form):
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'autocomplete': 'family-name'}))
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'autocomplete': 'given-name'}))
    middle_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'autocomplete': 'additional-name'}))
    no_middle_name = forms.BooleanField(required=False, label='I have no middle name')
    mobile = forms.CharField(label='Mobile number', help_text='We text your reminder here.', widget=forms.TextInput(attrs={'type': 'tel', 'autocomplete': 'tel', 'placeholder': '09XX XXX XXXX'}))
    email = forms.EmailField(max_length=150, help_text='We send your booking confirmation here.', widget=forms.EmailInput(attrs={'autocomplete': 'email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}), help_text='At least 8 characters.')
    privacy = forms.BooleanField(label='I have read the privacy notice and agree that my details are used to schedule my request.')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if get_user_model().objects.filter(Q(username__iexact=email) | Q(email__iexact=email)).exists():
            raise ValidationError('An account already uses this email. Please log in.')
        return email
    def clean_mobile(self):
        mobile = normalize_mobile(self.cleaned_data['mobile'])
        if not re.fullmatch(r'09\d{9}', mobile):
            raise ValidationError('Enter an 11-digit Philippine mobile number starting with 09.')
        if ResidentProfile.objects.filter(mobile=mobile).exists():
            raise ValidationError('An account already uses this mobile number.')
        return mobile
    def clean(self):
        data = super().clean()
        if data.get('no_middle_name'):
            data['middle_name'] = ''
        elif not data.get('middle_name'):
            self.add_error('middle_name', 'Enter your middle name or select “I have no middle name”.')
        if data.get('password'):
            user = get_user_model()(username=data.get('email', ''), email=data.get('email', ''), first_name=data.get('first_name', ''), last_name=data.get('last_name', ''))
            try:
                validate_password(data['password'], user)
            except ValidationError as exc:
                self.add_error('password', exc)
        return data
    @transaction.atomic
    def save(self):
        data = self.cleaned_data
        user = get_user_model().objects.create_user(username=data['email'], email=data['email'], password=data['password'], first_name=data['first_name'], last_name=data['last_name'])
        ResidentProfile.objects.create(user=user, mobile=data['mobile'], middle_name=data['middle_name'])
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Mobile number or email', widget=forms.TextInput(attrs={'autocomplete': 'username', 'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))

class ResetForm(forms.Form):
    identifier = forms.CharField(label='Mobile number or email', max_length=150, widget=forms.TextInput(attrs={'autocomplete': 'username'}))
    def save(self, request):
        identifier = self.cleaned_data['identifier'].strip()
        user = get_user_model().objects.filter(Q(email__iexact=identifier) | Q(resident_profile__mobile=normalize_mobile(identifier)), is_active=True).first()
        if user:
            form = PasswordResetForm({'email': user.email})
            if form.is_valid():
                form.save(request=request, use_https=request.is_secure(), email_template_name='accounts/reset_email.txt', subject_template_name='accounts/reset_subject.txt')

class BookingForm(forms.Form):
    documents = forms.ModelMultipleChoiceField(queryset=Document.objects.filter(bookable=True), widget=forms.CheckboxSelectMultiple, label='Choose your documents')
    slot = forms.ModelChoiceField(queryset=AppointmentSlot.objects.none(), empty_label='Choose a day and time', label='Available appointments')
    submission_key = forms.UUIDField(widget=forms.HiddenInput)
    prepared = forms.BooleanField(label='I have checked the requirements and will bring the original documents.')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slot'].queryset = AppointmentSlot.objects.filter(is_open=True, starts_at__gt=timezone.now(), reserved__lt=F('capacity'))
    def clean(self):
        data=super().clean()
        if data.get('slot') and data.get('documents'):
            from .scheduling import validate_slot
            try:
                validate_slot(data['slot'],data['documents'])
            except ValidationError as exc:
                self.add_error('slot',exc)
        return data

class RescheduleForm(forms.Form):
    slot = forms.ModelChoiceField(queryset=AppointmentSlot.objects.none(), label='New appointment')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from datetime import timedelta
        self.fields['slot'].queryset = AppointmentSlot.objects.filter(is_open=True, starts_at__gte=timezone.now()+timedelta(hours=24), reserved__lt=F('capacity'))

class ProfileForm(forms.ModelForm):
    middle_name = forms.CharField(max_length=100, required=False)
    address = forms.CharField(max_length=250, required=False, label='Residential address', widget=forms.TextInput(attrs={'autocomplete': 'street-address'}))
    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        profile = ResidentProfile.objects.filter(user=self.instance).first()
        if profile:
            self.fields['middle_name'].initial = profile.middle_name
            self.fields['address'].initial = profile.address
    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            ResidentProfile.objects.filter(user=user).update(middle_name=self.cleaned_data['middle_name'], address=self.cleaned_data['address'])
        return user
