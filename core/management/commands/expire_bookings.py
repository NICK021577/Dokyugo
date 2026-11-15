from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from core.models import AppointmentSlot, Booking, BookingEvent, Notification

class Command(BaseCommand):
    help = 'Mark confirmed, uncalled appointments as missed after the 15-minute grace period. Schedule every minute.'
    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(minutes=15)
        count = 0
        for pk in Booking.objects.filter(status='confirmed',checked_in_at__isnull=True, slot__starts_at__lt=cutoff).values_list('pk', flat=True):
            with transaction.atomic():
                booking = Booking.objects.select_for_update().get(pk=pk)
                if booking.status != 'confirmed' or booking.checked_in_at:
                    continue
                booking.status = 'missed'
                booking.save(update_fields=['status', 'updated_at'])
                AppointmentSlot.objects.filter(pk=booking.slot_id, reserved__gt=0).update(reserved=F('reserved')-1)
                text = f'{booking.ticket} was marked missed after the 15-minute grace period. You can book again.'
                BookingEvent.objects.create(booking=booking, description=text)
                Notification.objects.create(user=booking.resident, booking=booking, text=text)
                count += 1
        self.stdout.write(self.style.SUCCESS(f'Marked {count} booking(s) missed.'))
