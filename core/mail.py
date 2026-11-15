import logging
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from .models import Booking

logger = logging.getLogger(__name__)

def send_booking_email(booking_id, subject='Your DokyuGo booking is confirmed'):
    booking = Booking.objects.select_related('slot', 'resident').prefetch_related('documents').get(pk=booking_id)
    documents = ', '.join(d.name for d in booking.documents.all())
    appointment = timezone.localtime(booking.slot.starts_at).strftime('%A, %B %d, %Y at %I:%M %p')
    text = (f'Hello {booking.resident.first_name},\n\n{documents}\n'
            f'Appointment: {appointment}\nQueue number: {booking.ticket}\nWindow 1 · Booked\n\n'
            'Please bring your original requirements. You can change or cancel a booking up to 24 hours before your appointment.\n\nSalamat po!\nDokyuGo')
    try:
        return send_mail(subject, text, settings.DEFAULT_FROM_EMAIL, [booking.resident.email])
    except Exception:
        # Mail delivery failure must not undo a successfully reserved appointment.
        logger.exception('Could not deliver booking email for booking %s', booking.pk)
        return 0
