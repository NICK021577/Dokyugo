from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.mail import send_booking_email
from core.models import Booking, Notification

class Command(BaseCommand):
    help = 'Email reminders for tomorrow’s confirmed appointments. Schedule daily in Asia/Manila. No SMS provider is configured.'
    def handle(self, *args, **options):
        tomorrow = timezone.localdate() + timedelta(days=1)
        sent = 0
        for booking in Booking.objects.filter(date=tomorrow, status='confirmed', reminder_sent_at__isnull=True):
            if send_booking_email(booking.pk, 'Reminder: your DokyuGo appointment is tomorrow'):
                booking.reminder_sent_at = timezone.now()
                booking.save(update_fields=['reminder_sent_at'])
                Notification.objects.create(user=booking.resident, booking=booking, text=f'Reminder: {booking.ticket} is scheduled for tomorrow. Please bring your original requirements.')
                sent += 1
        self.stdout.write(self.style.SUCCESS(f'Sent {sent} email reminder(s).'))
