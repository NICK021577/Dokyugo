from datetime import timedelta
from urllib.parse import parse_qs,urlsplit
from django.core import signing
from django.core.exceptions import PermissionDenied,ValidationError
from django.db import transaction
from django.db.models import Case,F,IntegerField,Value,When
from django.utils import timezone
from .models import Booking,BookingEvent,DeskLock,DeskMessage,Notification,WalkIn,WalkInCounter,WalkInEvent

def staff_only(actor):
    if not actor.is_active or not actor.is_staff:
        raise PermissionDenied('Staff access is required.')

def admin_only(actor):
    if not actor.is_active or not actor.is_superuser:
        raise PermissionDenied('Administrator access is required.')

def priority_queue(items):
    return items.annotate(priority_order=Case(When(priority__in=['senior','pwd'],then=Value(0)),default=Value(1),output_field=IntegerField())).order_by('priority_order','checked_in_at','queue_number')

def ticket_token(booking):
    return signing.dumps({'booking':str(booking.pk)},salt='dokyugo-arrival-v1',compress=True)

def resolve_ticket(value):
    value=value.strip()
    if '://' in value or value.startswith('/'):
        value=parse_qs(urlsplit(value).query).get('ticket',[''])[0]
    try:
        payload=signing.loads(value,salt='dokyugo-arrival-v1',max_age=120*24*3600)
        return Booking.objects.select_related('resident','slot').prefetch_related('documents').get(pk=payload['booking'])
    except (signing.BadSignature,ValueError,KeyError,TypeError,ValidationError,Booking.DoesNotExist):
        raise ValidationError('This QR ticket is invalid or expired. Ask the resident to reopen their ticket.')

@transaction.atomic
def check_in(actor,booking_id):
    admin_only(actor)
    booking=Booking.objects.select_for_update().select_related('slot').get(pk=booking_id)
    if booking.status not in ['confirmed','called','processing']:
        raise ValidationError('This appointment is no longer available for arrival check-in.')
    if booking.checked_in_at:
        return booking,False
    now=timezone.now()
    if timezone.localtime(booking.slot.starts_at).date()!=timezone.localdate() or now<booking.slot.starts_at-timedelta(minutes=30):
        raise ValidationError('Check-in opens 30 minutes before the appointment, on its scheduled day.')
    if now>booking.slot.starts_at+timedelta(minutes=15):
        raise ValidationError('The 15-minute arrival grace period has ended. Arrange a new booking.')
    booking.checked_in_at=now
    booking.save(update_fields=['checked_in_at','updated_at'])
    BookingEvent.objects.create(booking=booking,actor=actor,description='Arrival checked in at the barangay desk.')
    Notification.objects.create(user=booking.resident,booking=booking,text=f'You are checked in for {booking.ticket}. Wait for Window 1 to call your number.')
    return booking,True

@transaction.atomic
def register_walkin(actor,data):
    admin_only(actor)
    counter,_=WalkInCounter.objects.get_or_create(date=timezone.localdate())
    WalkInCounter.objects.filter(pk=counter.pk).update(last_number=F('last_number')+1)
    counter.refresh_from_db()
    entry=WalkIn.objects.create(name=data['name'],mobile=data.get('mobile',''),priority=data['priority'],date=counter.date,queue_number=counter.last_number,registered_by=actor)
    entry.documents.set(data['documents'])
    WalkInEvent.objects.create(walkin=entry,actor=actor,description=f'Walk-in registered: {entry.get_priority_display()}.')
    return entry

@transaction.atomic
def walkin_transition(actor,pk,status):
    staff_only(actor)
    if not actor.is_superuser and status!='called':
        raise PermissionDenied('Staff may call residents and send messages. Administrators manage service status.')
    entry=WalkIn.objects.select_for_update().get(pk=pk)
    allowed={'waiting':['called','cancelled'],'called':['processing','cancelled'],'processing':['completed']}
    if status not in allowed.get(entry.status,[]):
        raise ValidationError('This queue action is no longer available. Refresh the queue.')
    now=timezone.now()
    if status=='called' and not entry.called_at:
        entry.called_at=now
    if status=='processing':
        entry.processing_started_at=now
    if status=='completed':
        entry.completed_at=now
    entry.status=status
    entry.save()
    WalkInEvent.objects.create(walkin=entry,actor=actor,description=f'{entry.ticket}: {entry.get_status_display()}.')
    return entry

@transaction.atomic
def call_next(actor,lane):
    staff_only(actor)
    if lane not in ['booked','walkin']:
        raise ValidationError('Choose Window 1 or Window 2.')
    lock,_=DeskLock.objects.get_or_create(date=timezone.localdate(),lane=lane)
    DeskLock.objects.select_for_update().get(pk=lock.pk)
    if lane=='booked':
        if Booking.objects.filter(date=lock.date,status__in=['called','processing']).exists():
            raise ValidationError('Window 1 is serving a resident. An administrator must finish the current service first.')
        booking=Booking.objects.filter(date=lock.date,status='confirmed',checked_in_at__isnull=False).order_by('slot__starts_at','queue_number').first()
        if not booking:
            raise ValidationError('No checked-in residents are waiting at Window 1.')
        from .services import staff_transition
        return staff_transition(actor,booking.pk,'called')
    if WalkIn.objects.filter(date=lock.date,status__in=['called','processing']).exists():
        raise ValidationError('Window 2 is serving a resident. Finish the current service before calling the next.')
    entry=priority_queue(WalkIn.objects.filter(date=lock.date,status='waiting')).first()
    if not entry:
        raise ValidationError('No walk-in residents are waiting at Window 2.')
    return walkin_transition(actor,entry.pk,'called')

@transaction.atomic
def recall(actor,lane,pk):
    staff_only(actor)
    if lane=='booked':
        entry=Booking.objects.select_for_update().get(pk=pk)
        if entry.status not in ['called','processing'] or entry.date!=timezone.localdate():
            raise ValidationError('Only the current resident can be called again.')
        BookingEvent.objects.create(booking=entry,actor=actor,description=f'{entry.ticket} called again at Window 1.')
        Notification.objects.create(user=entry.resident,booking=entry,text=f'{entry.ticket}: please proceed to Window 1. Your number is being called.')
    elif lane=='walkin':
        entry=WalkIn.objects.select_for_update().get(pk=pk)
        if entry.status not in ['called','processing'] or entry.date!=timezone.localdate():
            raise ValidationError('Only the current resident can be called again.')
        WalkInEvent.objects.create(walkin=entry,actor=actor,description=f'{entry.ticket} called again at Window 2.')
    else:
        raise ValidationError('Choose a valid service window.')
    return entry

@transaction.atomic
def send_message(actor,booking,body):
    if not actor.is_active:
        raise PermissionDenied('Sign-in access is required.')
    body=body.strip()
    if not body or len(body)>1000:
        raise ValidationError('Enter a message of 1–1000 characters.')
    if actor.pk!=booking.resident_id and not actor.is_staff:
        raise PermissionDenied('You cannot access this conversation.')
    if not booking.resident.is_active:
        raise ValidationError('This resident account cannot receive messages.')
    from .account_services import is_deleted
    if is_deleted(booking.resident):
        raise ValidationError('This account has been deleted.')
    message=DeskMessage.objects.create(booking=booking,sender=actor,body=body,read_by_staff=actor.is_staff,read_by_resident=actor.pk==booking.resident_id)
    if actor.is_staff:
        Notification.objects.create(user=booking.resident,booking=booking,text=('Message from the barangay: '+body)[:250])
    return message
