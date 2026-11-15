import json
import uuid
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .forms import RegistrationForm
from .models import AppointmentSlot, Booking, BookingEvent, Document, Notification, ResidentProfile
from . import services

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class DokyuGoTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(username='alex@example.com', email='alex@example.com', password='Correct-horse-91', first_name='Alex', last_name='Cruz')
        ResidentProfile.objects.create(user=self.user, mobile='09171234567')
        self.other = get_user_model().objects.create_user(username='other@example.com', email='other@example.com', password='Correct-horse-92')
        self.staff = get_user_model().objects.create_user(username='staff@example.com', password='Correct-horse-93', is_staff=True)
        self.doc = Document.objects.create(name='Barangay Clearance', slug='barangay-clearance', group='clearances', description='Proof of residency.')
        self.slot = AppointmentSlot.objects.create(starts_at=timezone.now()+timedelta(days=3), capacity=1)
        self.new_slot = AppointmentSlot.objects.create(starts_at=timezone.now()+timedelta(days=4), capacity=2)
    def make_booking(self, user=None, slot=None, key=None):
        return services.book(user or self.user, [self.doc], slot or self.slot, key or uuid.uuid4())
    def test_public_pages_render(self):
        for url in ['/', '/documents/', '/documents/?q=clearance', '/documents/?q=missing', '/documents/barangay-clearance/', '/how-it-works/', '/privacy/', '/login/', '/signup/', '/password-reset/']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
    def test_registration_and_mobile_login(self):
        data = {'last_name': 'Santos', 'first_name': 'Mia', 'no_middle_name': True, 'mobile': '+63 917 765 4321', 'email': 'MIA@example.com', 'password': 'Unique-passphrase-91!', 'privacy': True}
        response = self.client.post('/signup/', data)
        self.assertRedirects(response, '/resident/')
        user = get_user_model().objects.get(username='mia@example.com')
        self.assertTrue(user.check_password(data['password']))
        self.assertEqual(user.resident_profile.mobile, '09177654321')
        self.client.post('/logout/')
        self.assertRedirects(self.client.post('/login/', {'username': '+639177654321', 'password': data['password']}), '/resident/')
    def test_registration_validation(self):
        form = RegistrationForm({'last_name': 'Test', 'first_name': 'Test', 'mobile': '123', 'email': 'ALEX@example.com', 'password': '12345678'})
        self.assertFalse(form.is_valid())
        for field in ['middle_name', 'mobile', 'email', 'password', 'privacy']:
            self.assertIn(field, form.errors)
    def test_login_does_not_redirect_to_external_site(self):
        response = self.client.post('/login/?next=https://example.net', {'username': self.user.username, 'password': 'Correct-horse-91', 'next': 'https://example.net'})
        self.assertEqual(response.url, '/resident/')
    def test_login_rate_limit(self):
        for _ in range(10):
            self.client.post('/login/', {'username': self.user.username, 'password': 'incorrect'})
        response = self.client.post('/login/', {'username': self.user.username, 'password': 'Correct-horse-91'})
        self.assertContains(response, 'Too many attempts')
        self.assertNotIn('_auth_user_id', self.client.session)
    def test_booking_is_persistent_and_notifies(self):
        booking = self.make_booking()
        self.assertEqual(booking.ticket, 'B-001')
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.reserved, 1)
        self.assertEqual(booking.documents.get(), self.doc)
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 1)
        self.assertEqual(BookingEvent.objects.count(), 1)
    def test_capacity_is_enforced_and_transaction_rolls_back(self):
        self.make_booking()
        with self.assertRaises(ValidationError):
            self.make_booking(user=self.other)
        self.assertEqual(Booking.objects.count(), 1)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.reserved, 1)
    def test_double_submit_is_idempotent(self):
        key = uuid.uuid4()
        first = self.make_booking(key=key)
        second = self.make_booking(key=key)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Booking.objects.count(), 1)
        with self.assertRaises(ValidationError):
            self.make_booking(user=self.other, key=key)
    def test_cancel_releases_slot(self):
        booking = self.make_booking()
        services.cancel(self.user, booking.pk)
        self.slot.refresh_from_db()
        booking.refresh_from_db()
        self.assertEqual(self.slot.reserved, 0)
        self.assertEqual(booking.status, 'cancelled')
        with self.assertRaises(ValidationError):
            services.cancel(self.user, booking.pk)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.reserved, 0)
    def test_changes_blocked_inside_24_hours(self):
        self.slot.starts_at = timezone.now()+timedelta(hours=23)
        self.slot.save()
        booking = self.make_booking()
        with self.assertRaises(ValidationError):
            services.cancel(self.user, booking.pk)
        with self.assertRaises(ValidationError):
            services.reschedule(self.user, booking.pk, self.new_slot)
    def test_reschedule_moves_capacity_and_assigns_number_for_new_day(self):
        booking = self.make_booking()
        services.reschedule(self.user, booking.pk, self.new_slot)
        booking.refresh_from_db()
        self.slot.refresh_from_db()
        self.new_slot.refresh_from_db()
        self.assertEqual(booking.slot, self.new_slot)
        self.assertEqual(self.slot.reserved, 0)
        self.assertEqual(self.new_slot.reserved, 1)
        self.assertEqual(booking.date, timezone.localtime(self.new_slot.starts_at).date())
    def test_failed_reschedule_preserves_original_place(self):
        booking = self.make_booking()
        self.new_slot.is_open = False
        self.new_slot.save()
        with self.assertRaises(ValidationError):
            services.reschedule(self.user, booking.pk, self.new_slot)
        booking.refresh_from_db()
        self.slot.refresh_from_db()
        self.assertEqual(booking.slot_id, self.slot.pk)
        self.assertEqual(self.slot.reserved, 1)
    def test_private_pages_are_protected_and_isolated(self):
        booking = self.make_booking()
        self.assertEqual(self.client.get('/bookings/').status_code, 302)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('ticket', args=[booking.pk])).status_code, 404)
        self.assertEqual(self.client.get(f'/api/bookings/{booking.pk}/').status_code, 404)
        self.assertEqual(self.client.post(reverse('cancel', args=[booking.pk])).status_code, 404)
        self.assertEqual(self.client.get('/staff/').status_code, 403)
    def test_staff_status_changes_are_visible_to_resident(self):
        booking = self.make_booking()
        with self.assertRaises(ValidationError):
            services.staff_transition(self.user, booking.pk, 'called')
        services.staff_transition(self.staff, booking.pk, 'called')
        admin=get_user_model().objects.create_user('administrator',is_staff=True,is_superuser=True)
        for status in ['processing', 'completed']:
            services.staff_transition(admin, booking.pk, status)
        self.client.force_login(self.user)
        response = self.client.get(f'/api/bookings/{booking.pk}/')
        self.assertEqual(response.json()['status'], 'completed')
        with self.assertRaises(ValidationError):
            services.staff_transition(self.staff, booking.pk, 'called')
    def test_resident_and_staff_pages_render(self):
        booking = self.make_booking()
        self.client.force_login(self.user)
        for url in ['/resident/', '/bookings/', '/book/', '/profile/', '/profile/password/', '/notifications/', f'/bookings/{booking.pk}/', f'/bookings/{booking.pk}/cancel/', f'/bookings/{booking.pk}/reschedule/']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get('/staff/').status_code, 200)
    def test_password_reset_uses_email_for_mobile_and_hides_account_existence(self):
        response = self.client.post('/password-reset/', {'identifier': '09171234567'})
        self.assertContains(response, 'Check your email')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/reset/', mail.outbox[0].body)
        response = self.client.post('/password-reset/', {'identifier': 'unknown@example.com'})
        self.assertContains(response, 'Check your email')
        self.assertEqual(len(mail.outbox), 1)
    def test_reset_token_changes_password_and_is_single_use(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        response = self.client.get(f'/reset/{uid}/{token}/')
        self.assertEqual(response.status_code, 302)
        response = self.client.post(response.url, {'new_password1': 'Another-passphrase-37!', 'new_password2': 'Another-passphrase-37!'})
        self.assertRedirects(response, '/password-reset/complete/')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Another-passphrase-37!'))
        self.assertFalse(default_token_generator.check_token(self.user, token))
    def test_api_uses_the_same_database(self):
        self.assertEqual(self.client.get('/api/bookings/').status_code, 401)
        self.client.force_login(self.user)
        response = self.client.post('/api/bookings/', data=json.dumps({'documents': [self.doc.pk], 'slot': self.slot.pk, 'prepared': True, 'submission_key': str(uuid.uuid4())}), content_type='application/json')
        self.assertEqual(response.status_code, 201, response.content)
        booking_id = response.json()['id']
        self.assertContains(self.client.get(f'/bookings/{booking_id}/'), 'B-001')
        self.assertEqual(self.client.get('/api/bookings/').json()['bookings'][0]['id'], booking_id)
        self.assertEqual(self.client.post(f'/api/bookings/{booking_id}/cancel/').json()['status'], 'cancelled')
    def test_mutating_actions_require_post_and_csrf(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/logout/').status_code, 405)
        secure_client = Client(enforce_csrf_checks=True)
        self.assertEqual(secure_client.post('/api/login/', {'username': self.user.username, 'password': 'Correct-horse-91'}).status_code, 403)
        self.assertEqual(secure_client.post('/signup/', {}).status_code, 403)
    def test_malformed_api_input_is_rejected(self):
        self.client.force_login(self.user)
        for payload in ['{bad', '[]', 'null']:
            response = self.client.post('/api/bookings/', data=payload, content_type='application/json')
            self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get('/api/slots/?date=invalid').status_code, 400)

    def test_reminders_send_once_and_expiry_releases_place(self):
        from django.core.management import call_command
        from io import StringIO
        booking = self.make_booking()
        booking.date = timezone.localdate()+timedelta(days=1)
        booking.save()
        call_command('send_reminders', stdout=StringIO())
        call_command('send_reminders', stdout=StringIO())
        self.assertEqual(len(mail.outbox), 1)
        booking.refresh_from_db()
        self.assertIsNotNone(booking.reminder_sent_at)
        self.slot.starts_at = timezone.now()-timedelta(minutes=16)
        self.slot.save()
        call_command('expire_bookings', stdout=StringIO())
        booking.refresh_from_db()
        self.slot.refresh_from_db()
        self.assertEqual(booking.status, 'missed')
        self.assertEqual(self.slot.reserved, 0)

    def test_api_registration_and_notifications(self):
        payload = {'first_name': 'Mia', 'last_name': 'Cruz', 'no_middle_name': True, 'email': 'mia@example.com', 'mobile': '09179998888', 'password': 'Yet-another-passphrase-47!', 'privacy': True}
        response = self.client.post('/api/signup/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(self.client.get('/api/me/').json()['email'], 'mia@example.com')
        self.assertEqual(self.client.get('/api/notifications/').json(), {'notifications': []})
