import re
from datetime import timedelta
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .auth import normalize_mobile
from .management_forms import ScheduleForm
from .models import AppointmentSlot,Document,OpeningHours,ScheduleException,WalkIn

class WalkInForm(forms.Form):
    name=forms.CharField(max_length=150,label='Resident name')
    mobile=forms.CharField(max_length=30,required=False,label='Mobile number (optional)',widget=forms.TextInput(attrs={'type':'tel'}))
    priority=forms.ChoiceField(choices=WalkIn.Priority.choices,label='Queue priority')
    documents=forms.ModelMultipleChoiceField(queryset=Document.objects.all(),widget=forms.CheckboxSelectMultiple,label='Requested documents')
    def clean_mobile(self):
        mobile=normalize_mobile(self.cleaned_data['mobile'])
        if mobile and not re.fullmatch(r'09\d{9}',mobile):
            raise ValidationError('Enter an 11-digit mobile number starting with 09, or leave this empty.')
        return mobile

class MessageForm(forms.Form):
    body=forms.CharField(max_length=1000,label='Message',widget=forms.Textarea(attrs={'rows':4,'placeholder':'Write a message to the resident…'}))

class CheckInForm(forms.Form):
    ticket=forms.CharField(max_length=2000,label='QR ticket or ticket link',widget=forms.Textarea(attrs={'rows':3,'placeholder':'Scan with a USB scanner or paste the QR ticket link'}))

class PublishForm(ScheduleForm):
    documents=forms.ModelMultipleChoiceField(queryset=Document.objects.all(),required=False,widget=forms.CheckboxSelectMultiple,label='Services available (leave empty for all)')
    break_start=forms.TimeField(required=False,widget=forms.TimeInput(attrs={'type':'time'}),label='Break starts (optional)')
    break_end=forms.TimeField(required=False,widget=forms.TimeInput(attrs={'type':'time'}),label='Break ends (optional)')
    def clean(self):
        data=super().clean()
        start,end=data.get('break_start'),data.get('break_end')
        if bool(start)!=bool(end):
            self.add_error('break_end','Enter both break times, or leave both empty.')
        elif start and end:
            if start>=end or (data.get('start_time') and start<data['start_time']) or (data.get('end_time') and end>data['end_time']):
                self.add_error('break_end','The break must be within opening hours and end after it starts.')
        return data

class OpeningHoursForm(PublishForm):
    name=forms.CharField(max_length=100,label='Schedule name')
    weekdays=forms.TypedMultipleChoiceField(choices=list(enumerate(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])),coerce=int,initial=[0,1,2,3,4],widget=forms.CheckboxSelectMultiple,label='Repeat on')
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        del self.fields['weekdays_only']
        self.order_fields(['name','start_date','end_date','weekdays','start_time','end_time','break_start','break_end','interval','capacity','documents'])

class ExceptionForm(forms.ModelForm):
    class Meta:
        model=ScheduleException
        fields=['name','kind','starts_at','ends_at','documents']
        labels={'starts_at':'Unavailable from','ends_at':'Available again at','documents':'Affected services (leave empty for all)'}
        widgets={'starts_at':forms.DateTimeInput(format='%Y-%m-%dT%H:%M',attrs={'type':'datetime-local'}),'ends_at':forms.DateTimeInput(format='%Y-%m-%dT%H:%M',attrs={'type':'datetime-local'}),'documents':forms.CheckboxSelectMultiple}
    def clean(self):
        data=super().clean()
        start,end=data.get('starts_at'),data.get('ends_at')
        if start and end and end<=start:
            self.add_error('ends_at','The reopening time must be after the closure starts.')
        if end and end<=timezone.now():
            self.add_error('ends_at','Choose a period that has not already ended.')
        return data

class SlotEditorForm(forms.ModelForm):
    class Meta:
        model=AppointmentSlot
        fields=['capacity','duration_minutes','is_open','documents']
        widgets={'documents':forms.CheckboxSelectMultiple}
        labels={'is_open':'Accept new bookings','documents':'Allowed services (leave empty for all)','duration_minutes':'Appointment duration in minutes'}
    def clean_capacity(self):
        value=self.cleaned_data['capacity']
        if not max(1,self.instance.reserved)<=value<=50:
            raise ValidationError(f'Choose {max(1,self.instance.reserved)}–50 places. Existing reservations cannot be removed.')
        return value
    def clean_documents(self):
        documents=self.cleaned_data['documents']
        allowed=set(documents.values_list('pk',flat=True))
        if allowed:
            existing=set(Document.objects.filter(booking__slot=self.instance,booking__status__in=['confirmed','called','processing']).values_list('pk',flat=True))
            if not existing.issubset(allowed):
                raise ValidationError('The selected services would exclude an existing active booking. Retain those services or choose all.')
        return documents

class ReportFilterForm(forms.Form):
    start=forms.DateField(label='From',widget=forms.DateInput(attrs={'type':'date'}))
    end=forms.DateField(label='Through',widget=forms.DateInput(attrs={'type':'date'}))
    lane=forms.ChoiceField(choices=[('all','All windows'),('booked','Window 1 · Booked'),('walkin','Window 2 · Walk-in')],required=False)
    document=forms.ModelChoiceField(queryset=Document.objects.all(),required=False,empty_label='All documents')
    def clean(self):
        data=super().clean()
        if data.get('start') and data.get('end') and (data['end']<data['start'] or data['end']-data['start']>timedelta(days=365)):
            self.add_error('end','Choose a date range of up to one year ending after the start date.')
        return data
