import calendar
import re
from datetime import date, datetime, time, timedelta
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from .models import AppointmentSlot, Booking,Document,ScheduleException
from .scheduling import slot_reason

def picker_context(form, booking=None):
    value = form['slot'].value()
    selected = None
    try:
        selected = AppointmentSlot.objects.filter(pk=int(value)).first() if value else None
    except (TypeError, ValueError, OverflowError):
        pass
    minimum = timezone.now() + (timedelta(hours=24) if booking else timedelta())
    first = selected or form.fields['slot'].queryset.first()
    initial_date = timezone.localtime(first.starts_at).date() if first else timezone.localdate()
    url = reverse('api_availability')
    if booking:
        url += f'?reschedule={booking.pk}'
    return {'endpoint': url, 'month': initial_date.strftime('%Y-%m'), 'selectedDate': initial_date.isoformat(),
            'selectedSlot': str(selected.pk) if selected else '', 'today': timezone.localdate().isoformat(),
            'minMonth': timezone.localdate().strftime('%Y-%m'),
            'maxMonth': (timezone.localdate()+timedelta(days=365)).strftime('%Y-%m')}

@require_GET
@never_cache
def api_availability(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please log in to view appointment availability.'}, status=401)
    today = timezone.localdate()
    raw = request.GET.get('month', today.strftime('%Y-%m'))
    try:
        if not re.fullmatch(r'\d{4}-\d{2}', raw):
            raise ValueError
        first = date.fromisoformat(raw+'-01')
    except ValueError:
        return JsonResponse({'error': 'Choose a month in YYYY-MM format.'}, status=400)
    if raw < today.strftime('%Y-%m') or raw > (today+timedelta(days=365)).strftime('%Y-%m'):
        return JsonResponse({'error': 'Choose a month within the next year.'}, status=400)
    booking = None
    if request.GET.get('reschedule'):
        import uuid
        try:
            booking_id = uuid.UUID(request.GET['reschedule'])
        except ValueError:
            return JsonResponse({'error': 'Invalid booking.'}, status=400)
        booking = get_object_or_404(Booking.objects.select_related('slot'), pk=booking_id, resident=request.user)
        if not booking.can_change:
            return JsonResponse({'error': 'This booking can no longer be rescheduled.'}, status=400)
    last = first+timedelta(days=calendar.monthrange(first.year, first.month)[1])
    docs=list(booking.documents.all()) if booking else []
    raw_docs=request.GET.get('documents','')
    if raw_docs:
        try:
            ids={int(value) for value in raw_docs.split(',')}
            if len(ids)>30 or any(pk<=0 for pk in ids):
                raise ValueError
        except ValueError:
            return JsonResponse({'error':'Choose valid documents.'},status=400)
        docs=list(Document.objects.filter(pk__in=ids,bookable=True))
        if len(docs)!=len(ids):
            return JsonResponse({'error':'One of the selected documents is not available for booking.'},status=400)
    minimum = timezone.now()+(timedelta(hours=24) if booking else timedelta())
    starts=timezone.make_aware(datetime.combine(first,time.min))
    ends=timezone.make_aware(datetime.combine(last,time.min))
    slots = AppointmentSlot.objects.filter(starts_at__gte=starts, starts_at__lt=ends).prefetch_related('documents')
    exceptions=list(ScheduleException.objects.filter(active=True,starts_at__lt=ends+timedelta(hours=4),ends_at__gt=starts).prefetch_related('documents'))
    days = {}
    for slot in slots:
        local = timezone.localtime(slot.starts_at)
        key = local.date().isoformat()
        blocked=slot_reason(slot,docs,exceptions)
        available = slot.is_open and slot.remaining > 0 and slot.starts_at > minimum and not blocked and (not booking or slot.pk != booking.slot_id)
        reason = ''
        if not available:
            reason = 'Past time' if slot.starts_at <= minimum else 'Closed' if not slot.is_open else 'Current appointment' if booking and slot.pk == booking.slot_id else blocked or 'Full'
        entry = days.setdefault(key, {'date': key, 'remaining': 0, 'slots': []})
        if available:
            entry['remaining'] += slot.remaining
        entry['slots'].append({'id': slot.pk, 'starts_at': local.isoformat(), 'time': local.strftime('%I:%M %p').lstrip('0'), 'remaining': slot.remaining, 'available': available, 'reason': reason})
    response = JsonResponse({'month': raw, 'timezone': 'Asia/Manila', 'days': list(days.values())})
    return response
