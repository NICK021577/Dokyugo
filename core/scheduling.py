from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .models import AppointmentSlot, Booking, BookingEvent, Notification, OpeningHours, ScheduleException

def document_ids(documents):
    return {getattr(doc,'pk',doc) for doc in documents}

def slot_reason(slot, documents=(), exceptions=None):
    selected=document_ids(documents)
    allowed={doc.pk for doc in slot.documents.all()}
    if selected and allowed and not selected.issubset(allowed):
        return 'Different service'
    end=slot.starts_at+timedelta(minutes=slot.duration_minutes)
    if exceptions is None:
        exceptions=ScheduleException.objects.filter(active=True,starts_at__lt=end,ends_at__gt=slot.starts_at).prefetch_related('documents')
    for exception in exceptions:
        if exception.starts_at >= end or exception.ends_at <= slot.starts_at:
            continue
        scope={doc.pk for doc in exception.documents.all()}
        if not scope or (selected and scope.intersection(selected)):
            return exception.name
    return ''

def validate_slot(slot,documents=()):
    reason=slot_reason(slot,documents)
    if reason:
        raise ValidationError(f'This appointment is unavailable for your documents: {reason}. Choose another time.')

def occurrences(data, *, start=None, end=None):
    first=max(data['start_date'], start or data['start_date'], timezone.localdate())
    last=min(data['end_date'],end or data['end_date'])
    weekdays=set(data.get('weekdays',range(5) if data.get('weekdays_only') else range(7)))
    day=first
    step=timedelta(minutes=int(data['interval']))
    while day<=last:
        if day.weekday() in weekdays:
            moment=timezone.make_aware(datetime.combine(day,data['start_time']))
            finish=timezone.make_aware(datetime.combine(day,data['end_time']))
            pause_start=timezone.make_aware(datetime.combine(day,data['break_start'])) if data.get('break_start') else None
            pause_end=timezone.make_aware(datetime.combine(day,data['break_end'])) if data.get('break_end') else None
            while moment+step<=finish:
                overlaps=pause_start and moment<pause_end and moment+step>pause_start
                if moment>timezone.now() and not overlaps:
                    yield moment
                moment+=step
        day+=timedelta(days=1)

@transaction.atomic
def publish(data, *, start=None, end=None):
    docs=list(data.get('documents',[]))
    created,existing,blocked=0,0,0
    for moment in occurrences(data,start=start,end=end):
        # Test closure/service exceptions without creating a database row first.
        candidate=AppointmentSlot(starts_at=moment,duration_minutes=int(data['interval']))
        # Unsaved slots cannot have a M2M manager; use the exception overlap check.
        overlaps=ScheduleException.objects.filter(active=True,starts_at__lt=moment+timedelta(minutes=int(data['interval'])),ends_at__gt=moment).prefetch_related('documents')
        selected=document_ids(docs)
        if any(not set(e.documents.values_list('pk',flat=True)) or (selected and selected.intersection(e.documents.values_list('pk',flat=True))) for e in overlaps):
            blocked+=1
            continue
        slot,added=AppointmentSlot.objects.get_or_create(starts_at=moment,defaults={'capacity':data['capacity'],'duration_minutes':int(data['interval'])})
        if added:
            slot.documents.set(docs)
            created+=1
        else:
            existing+=1
    return {'created':created,'existing':existing,'blocked':blocked}

def rule_data(rule):
    return {key:getattr(rule,key) for key in ['start_date','end_date','weekdays','start_time','end_time','break_start','break_end','interval','capacity']}|{'documents':list(rule.documents.all())}

def affected_bookings(exception):
    # Include appointments whose time overlaps the exception, including slots
    # starting shortly before it. Slot durations are bounded to at most 240m.
    items=Booking.objects.filter(status='confirmed',slot__starts_at__lt=exception.ends_at,slot__starts_at__gte=exception.starts_at-timedelta(hours=4)).select_related('slot','resident').prefetch_related('documents')
    scope={doc.pk for doc in exception.documents.all()}
    return [b for b in items if b.slot.starts_at+timedelta(minutes=b.slot.duration_minutes)>exception.starts_at and (not scope or scope.intersection(d.pk for d in b.documents.all()))]

def notify_exception(exception,actor, *, reopening=False):
    bookings=affected_bookings(exception)
    for booking in bookings:
        text=(f'Calendar notice: {exception.name} was lifted. Check your appointment details.' if reopening else f'Calendar notice: your {booking.ticket} appointment is affected by {exception.name}. Contact the barangay or reschedule. Your booking is retained.')
        Notification.objects.create(user=booking.resident,booking=booking,text=text[:250])
        BookingEvent.objects.create(booking=booking,actor=actor,description=text[:250])
    return len(bookings)
