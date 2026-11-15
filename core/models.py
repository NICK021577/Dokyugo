import uuid
from datetime import datetime, timedelta
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.core.validators import MinValueValidator,MaxValueValidator

class ResidentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resident_profile')
    middle_name = models.CharField(max_length=100, blank=True)
    mobile = models.CharField(max_length=11, unique=True)
    address = models.CharField(max_length=250, blank=True)
    demo_expires_at = models.DateTimeField(null=True, blank=True)
    privacy_accepted_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Document(models.Model):
    class Group(models.TextChoices):
        CLEARANCE = 'clearances', 'Clearances'
        CERTIFICATE = 'certifications', 'Certifications'
        LEGAL = 'legal', 'Legal and other documents'
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, max_length=160)
    group = models.CharField(max_length=20, choices=Group.choices)
    description = models.TextField()
    icon = models.CharField(max_length=20, default='Doc')
    fee = models.CharField(max_length=100, default='[AMOUNT TO CONFIRM]')
    processing_time = models.CharField(max_length=100, default='[TO CONFIRM]')
    bookable = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['position', 'name']
    def __str__(self):
        return self.name

class Requirement(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='requirements')
    text = models.CharField(max_length=250)
    position = models.PositiveIntegerField(default=0)
    confirmed = models.BooleanField(default=False)
    class Meta:
        ordering = ['position', 'pk']
    def __str__(self):
        return self.text

class AppointmentSlot(models.Model):
    starts_at = models.DateTimeField(unique=True)
    capacity = models.PositiveSmallIntegerField(default=5)
    reserved = models.PositiveSmallIntegerField(default=0)
    is_open = models.BooleanField(default=True)
    duration_minutes = models.PositiveSmallIntegerField(default=30,validators=[MinValueValidator(1),MaxValueValidator(240)])
    documents = models.ManyToManyField(Document,blank=True,related_name='appointment_slots')
    class Meta:
        ordering = ['starts_at']
        constraints = [models.CheckConstraint(condition=Q(reserved__lte=models.F('capacity')), name='slot_within_capacity')]
    @property
    def remaining(self):
        return self.capacity - self.reserved
    def __str__(self):
        return timezone.localtime(self.starts_at).strftime('%a, %b %d · %I:%M %p')

class QueueCounter(models.Model):
    date = models.DateField(unique=True)
    last_number = models.PositiveIntegerField(default=0)

class Booking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = 'confirmed', 'Confirmed'
        CALLED = 'called', 'Now serving'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        MISSED = 'missed', 'Missed'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resident = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='bookings')
    documents = models.ManyToManyField(Document)
    slot = models.ForeignKey(AppointmentSlot, on_delete=models.PROTECT, related_name='bookings')
    date = models.DateField()
    queue_number = models.PositiveIntegerField()
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.CONFIRMED)
    submission_key = models.UUIDField(unique=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    checked_in_at = models.DateTimeField(null=True,blank=True)
    called_at = models.DateTimeField(null=True,blank=True)
    processing_started_at = models.DateTimeField(null=True,blank=True)
    completed_at = models.DateTimeField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['date', 'queue_number'], name='unique_daily_queue'),
            models.UniqueConstraint(fields=['resident', 'slot'], condition=Q(status__in=['confirmed', 'called', 'processing']), name='one_active_booking_per_slot'),
        ]
    @property
    def ticket(self):
        return f'B-{self.queue_number:03d}'
    @property
    def can_change(self):
        return self.status == self.Status.CONFIRMED and self.slot.starts_at - timezone.now() >= timedelta(hours=24)
    def __str__(self):
        return f'{self.ticket} · {self.date} · {self.resident.get_full_name()}'

class BookingEvent(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='events')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    description = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='notifications')
    text = models.CharField(max_length=250)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']

class AdminActivity(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']

class AccountLifecycle(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='account_lifecycle')
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_accounts')

class WalkInCounter(models.Model):
    date = models.DateField(unique=True)
    last_number = models.PositiveIntegerField(default=0)

class WalkIn(models.Model):
    class Priority(models.TextChoices):
        REGULAR='regular','Regular'
        SENIOR='senior','Senior citizen'
        PWD='pwd','Person with disability'
    class Status(models.TextChoices):
        WAITING='waiting','Waiting'
        CALLED='called','Now serving'
        PROCESSING='processing','Processing'
        COMPLETED='completed','Completed'
        CANCELLED='cancelled','Cancelled'
    name=models.CharField(max_length=150)
    mobile=models.CharField(max_length=11,blank=True)
    documents=models.ManyToManyField(Document)
    priority=models.CharField(max_length=10,choices=Priority.choices,default=Priority.REGULAR)
    date=models.DateField(default=timezone.localdate)
    queue_number=models.PositiveIntegerField()
    registered_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    status=models.CharField(max_length=15,choices=Status.choices,default=Status.WAITING)
    checked_in_at=models.DateTimeField(default=timezone.now)
    called_at=models.DateTimeField(null=True,blank=True)
    processing_started_at=models.DateTimeField(null=True,blank=True)
    completed_at=models.DateTimeField(null=True,blank=True)
    class Meta:
        ordering=['checked_in_at','pk']
        constraints=[models.UniqueConstraint(fields=['date','queue_number'],name='unique_daily_walkin')]
    @property
    def ticket(self):
        return f'W-{self.queue_number:03d}'

class WalkInEvent(models.Model):
    walkin=models.ForeignKey(WalkIn,on_delete=models.CASCADE,related_name='events')
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True)
    description=models.CharField(max_length=250)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['-created_at']

class DeskLock(models.Model):
    date=models.DateField()
    lane=models.CharField(max_length=10)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['date','lane'],name='unique_desk_lock')]

class DeskMessage(models.Model):
    booking=models.ForeignKey(Booking,on_delete=models.CASCADE,related_name='messages')
    sender=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    body=models.CharField(max_length=1000)
    read_by_staff=models.BooleanField(default=False)
    read_by_resident=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['created_at','pk']

def default_weekdays():
    return [0,1,2,3,4]

class OpeningHours(models.Model):
    name=models.CharField(max_length=100)
    start_date=models.DateField()
    end_date=models.DateField()
    weekdays=models.JSONField(default=default_weekdays)
    start_time=models.TimeField()
    end_time=models.TimeField()
    break_start=models.TimeField(null=True,blank=True)
    break_end=models.TimeField(null=True,blank=True)
    interval=models.PositiveSmallIntegerField(default=30)
    capacity=models.PositiveSmallIntegerField(default=5)
    documents=models.ManyToManyField(Document,blank=True)
    active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['name','pk']

class ScheduleException(models.Model):
    class Kind(models.TextChoices):
        HOLIDAY='holiday','Holiday / full-day closure'
        BREAK='break','Break / unavailable period'
        SERVICE='service','Service exception'
    name=models.CharField(max_length=150)
    kind=models.CharField(max_length=10,choices=Kind.choices,default=Kind.HOLIDAY)
    starts_at=models.DateTimeField()
    ends_at=models.DateTimeField()
    documents=models.ManyToManyField(Document,blank=True)
    active=models.BooleanField(default=True)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['-starts_at']
        constraints=[models.CheckConstraint(condition=Q(ends_at__gt=models.F('starts_at')),name='exception_valid_range')]
