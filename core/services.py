from datetime import timedelta
from django.core.exceptions import ValidationError,PermissionDenied
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .models import AppointmentSlot, Booking, BookingEvent, Document, Notification, QueueCounter

def _reserve(slot_id,documents=()):
    slot=AppointmentSlot.objects.select_for_update().prefetch_related('documents').get(pk=slot_id)
    from .scheduling import validate_slot
    validate_slot(slot,documents)
    count = AppointmentSlot.objects.filter(pk=slot_id, is_open=True, starts_at__gt=timezone.now(), reserved__lt=F('capacity')).update(reserved=F('reserved')+1)
    if not count:
        raise ValidationError('That appointment is no longer available. Please choose another time.')
    return AppointmentSlot.objects.get(pk=slot_id)

def _number(date):
    counter, _ = QueueCounter.objects.get_or_create(date=date)
    QueueCounter.objects.filter(pk=counter.pk).update(last_number=F('last_number')+1)
    counter.refresh_from_db()
    return counter.last_number

def _record(booking, actor, text):
    BookingEvent.objects.create(booking=booking, actor=actor, description=text)
    Notification.objects.create(user=booking.resident, booking=booking, text=text)

@transaction.atomic
def book(user, documents, slot, submission_key):
    existing = Booking.objects.filter(submission_key=submission_key).first()
    if existing:
        if existing.resident_id != user.pk:
            raise ValidationError('Please refresh the booking form and try again.')
        return existing
    if not documents or Document.objects.filter(pk__in=[d.pk for d in documents], bookable=False).exists():
        raise ValidationError('Choose documents that are available for booking.')
    if Booking.objects.filter(resident=user, slot=slot, status__in=['confirmed', 'called', 'processing']).exists():
        raise ValidationError('You already have an active booking for this time.')
    slot = _reserve(slot.pk,documents)
    date = timezone.localtime(slot.starts_at).date()
    booking = Booking.objects.create(resident=user, slot=slot, date=date, queue_number=_number(date), submission_key=submission_key)
    booking.documents.set(documents)
    _record(booking, user, f'Booking confirmed. Your queue number is {booking.ticket}.')
    from .mail import send_booking_email
    transaction.on_commit(lambda: send_booking_email(booking.pk))
    return booking

@transaction.atomic
def cancel(user, booking_id):
    booking = Booking.objects.select_for_update().select_related('slot').get(pk=booking_id, resident=user)
    if not booking.can_change:
        raise ValidationError('You can cancel a confirmed booking up to 24 hours before the appointment.')
    booking.status = Booking.Status.CANCELLED
    booking.save(update_fields=['status', 'updated_at'])
    AppointmentSlot.objects.filter(pk=booking.slot_id, reserved__gt=0).update(reserved=F('reserved')-1)
    _record(booking, user, f'{booking.ticket} was cancelled. Your place is now available to another resident.')
    return booking

@transaction.atomic
def reschedule(user, booking_id, new_slot):
    booking = Booking.objects.select_for_update().select_related('slot').get(pk=booking_id, resident=user)
    if not booking.can_change or new_slot.starts_at < timezone.now()+timedelta(hours=24):
        raise ValidationError('Changes must be made at least 24 hours before both appointments.')
    if booking.slot_id == new_slot.pk:
        raise ValidationError('Choose a different appointment.')
    if Booking.objects.filter(resident=user, slot=new_slot, status__in=['confirmed', 'called', 'processing']).exists():
        raise ValidationError('You already have an active booking for this time.')
    slot = _reserve(new_slot.pk,booking.documents.all())
    AppointmentSlot.objects.filter(pk=booking.slot_id, reserved__gt=0).update(reserved=F('reserved')-1)
    date = timezone.localtime(slot.starts_at).date()
    if date != booking.date:
        booking.queue_number = _number(date)
    booking.date, booking.slot = date, slot
    booking.reminder_sent_at = None
    booking.checked_in_at = None
    booking.save()
    _record(booking, user, f'Booking rescheduled. Your queue number is {booking.ticket}.')
    from .mail import send_booking_email
    transaction.on_commit(lambda: send_booking_email(booking.pk, 'Your DokyuGo booking was rescheduled'))
    return booking

@transaction.atomic
def staff_transition(actor, booking_id, status):
    if not actor.is_active or not actor.is_staff:
        raise ValidationError('Staff access is required.')
    if not actor.is_superuser and status!='called':
        raise PermissionDenied('Staff may call residents and send messages. Administrators manage service status.')
    booking = Booking.objects.select_for_update().get(pk=booking_id)
    allowed = {'confirmed': ['called', 'missed'], 'called': ['processing', 'missed'], 'processing': ['completed']}
    if status not in allowed.get(booking.status, []):
        raise ValidationError('That status change is not available. Refresh the queue.')
    booking.status = status
    now=timezone.now()
    if status=='called' and not booking.called_at:
        booking.called_at=now
    if status=='processing':
        booking.processing_started_at=now
    if status=='completed':
        booking.completed_at=now
    if status=='missed':
        AppointmentSlot.objects.filter(pk=booking.slot_id,reserved__gt=0).update(reserved=F('reserved')-1)
    booking.save(update_fields=['status','called_at','processing_started_at','completed_at','updated_at'])
    _record(booking, actor, f'{booking.ticket}: {booking.get_status_display()}.')
    return booking
