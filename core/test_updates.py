import json
import uuid
from datetime import datetime, time, timedelta
from io import StringIO
from django.contrib.auth import authenticate, get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .models import AdminActivity, AppointmentSlot, Booking, Document, Requirement, ResidentProfile
from . import services

class AdministrationAndCalendarTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.admin=User.objects.create_user('admin@test.local', password='Strong-test-passphrase-81', is_staff=True, is_superuser=True)
        self.staff=User.objects.create_user('staff@test.local', password='Strong-test-passphrase-82', is_staff=True)
        self.resident=User.objects.create_user('resident@test.local', password='Strong-test-passphrase-83', first_name='Alex')
        self.doc=Document.objects.create(name='Barangay Clearance', slug='barangay-clearance', group='clearances', description='Resident document')
        self.day=timezone.localdate()+timedelta(days=3)
        self.slot=AppointmentSlot.objects.create(starts_at=timezone.make_aware(datetime.combine(self.day,time(9))), capacity=2)
        self.full=AppointmentSlot.objects.create(starts_at=timezone.make_aware(datetime.combine(self.day,time(10))), capacity=1, reserved=1)
        self.closed=AppointmentSlot.objects.create(starts_at=timezone.make_aware(datetime.combine(self.day,time(11))), is_open=False)
    def test_role_specific_login_redirects(self):
        for user, suffix, expected in [(self.admin,'81','/management/'),(self.staff,'82','/staff/'),(self.resident,'83','/resident/')]:
            self.client.logout()
            response=self.client.post('/login/',{'username':user.username,'password':'Strong-test-passphrase-'+suffix})
            self.assertEqual(response.url,expected)
    def test_management_requires_administrator(self):
        paths=['/management/','/management/schedule/','/management/documents/','/management/accounts/','/management/activity/']
        for user in [self.staff,self.resident]:
            self.client.force_login(user)
            for path in paths:
                with self.subTest(user=user.username,path=path):
                    self.assertEqual(self.client.get(path).status_code,403)
        self.client.force_login(self.admin)
        for path in paths+[f'/management/documents/{self.doc.pk}/','/management/documents/new/']:
            self.assertEqual(self.client.get(path).status_code,200)
    def test_publish_schedule_preserves_existing_slots(self):
        self.client.force_login(self.admin)
        payload={'start_date':str(self.day),'end_date':str(self.day),'start_time':'09:00','end_time':'11:00','interval':30,'capacity':4}
        self.client.post('/management/schedule/',payload)
        self.assertEqual(AppointmentSlot.objects.filter(starts_at__date=self.day).count(),5)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.capacity,2)
        self.assertEqual(AdminActivity.objects.count(),1)
    def test_schedule_validation_rejects_backwards_and_long_ranges(self):
        self.client.force_login(self.admin)
        payload={'start_date':str(self.day),'end_date':str(self.day+timedelta(days=100)),'start_time':'16:00','end_time':'08:00','interval':30,'capacity':5}
        response=self.client.post('/management/schedule/',payload)
        self.assertEqual(response.status_code,200)
        self.assertEqual(AppointmentSlot.objects.count(),3)
        self.assertContains(response,'finish time must be after')
    def test_capacity_cannot_go_below_reservations_and_close_preserves_bookings(self):
        self.client.force_login(self.admin)
        booking=services.book(self.resident,[self.doc],self.slot,uuid.uuid4())
        self.client.post(reverse('management_slot',args=[self.slot.pk]),{'action':'capacity','capacity':0})
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.capacity,2)
        self.client.post(reverse('management_slot',args=[self.slot.pk]),{'action':'toggle'})
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_open)
        self.assertEqual(Booking.objects.get(pk=booking.pk).status,'confirmed')
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(reverse('management_slot',args=[self.slot.pk]),{'action':'toggle'}).status_code,403)
    def test_document_changes_reach_public_and_mobile_api(self):
        self.client.force_login(self.admin)
        response=self.client.post(reverse('management_document',args=[self.doc.pk]),{'name':self.doc.name,'group':'clearances','description':'Bring these updated documents.','fee':'To be confirmed by staff','processing_time':'Upon verification','bookable':True,'requirements_text':'Valid resident ID\nProof of address','requirements_verified':True})
        self.assertRedirects(response,'/management/documents/')
        self.assertEqual(list(self.doc.requirements.values_list('text',flat=True)),['Valid resident ID','Proof of address'])
        self.assertTrue(all(self.doc.requirements.values_list('confirmed',flat=True)))
        self.assertContains(self.client.get('/documents/barangay-clearance/'),'Proof of address')
        api=self.client.get('/api/documents/').json()
        self.assertEqual(api['documents'][0]['description'],'Bring these updated documents.')
    def test_account_access_and_protected_admin(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('management_account',args=[self.resident.pk]),{'role':'staff','active':True})
        self.resident.refresh_from_db()
        self.assertTrue(self.resident.is_staff)
        self.client.post(reverse('management_account',args=[self.resident.pk]),{'role':'resident'})
        self.resident.refresh_from_db()
        self.assertFalse(self.resident.is_active)
        self.assertEqual(self.client.post(reverse('management_account',args=[self.admin.pk]),{'role':'resident'}).status_code,403)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_superuser)
    def test_monthly_availability_is_current_and_marks_full_and_closed(self):
        self.assertEqual(self.client.get('/api/availability/').status_code,401)
        self.client.force_login(self.resident)
        data=self.client.get('/api/availability/',{'month':self.day.strftime('%Y-%m')}).json()
        day=next(row for row in data['days'] if row['date']==str(self.day))
        self.assertEqual(day['remaining'],2)
        slots={row['id']:row for row in day['slots']}
        self.assertTrue(slots[self.slot.pk]['available'])
        self.assertEqual(slots[self.full.pk]['reason'],'Full')
        self.assertEqual(slots[self.closed.pk]['reason'],'Closed')
        self.assertEqual(data['timezone'],'Asia/Manila')
        for month in ['bad','2026-15','2026-1','2099-01']:
            self.assertEqual(self.client.get('/api/availability/',{'month':month}).status_code,400)
    def test_reschedule_calendar_ownership_and_current_time(self):
        booking=services.book(self.resident,[self.doc],self.slot,uuid.uuid4())
        self.client.force_login(self.resident)
        response=self.client.get('/api/availability/',{'month':self.day.strftime('%Y-%m'),'reschedule':str(booking.pk)})
        day=next(row for row in response.json()['days'] if row['date']==str(self.day))
        self.assertEqual(next(row for row in day['slots'] if row['id']==self.slot.pk)['reason'],'Current appointment')
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get('/api/availability/',{'reschedule':str(booking.pk)}).status_code,404)
    @override_settings(DEBUG=True)
    def test_demo_accounts_expire_and_existing_password_is_preserved(self):
        call_command('create_demo_accounts',stdout=StringIO())
        user=get_user_model().objects.get(username='user@dokyugo.test')
        self.assertIsNotNone(authenticate(username=user.username,password='UserDemo!2026'))
        with override_settings(DEBUG=False):
            self.assertIsNone(authenticate(username=user.username,password='UserDemo!2026'))
        user.set_password('Changed-test-passphrase-44')
        user.save()
        call_command('create_demo_accounts',stdout=StringIO())
        user.refresh_from_db()
        self.assertTrue(user.check_password('Changed-test-passphrase-44'))
        ResidentProfile.objects.filter(user=user).update(demo_expires_at=timezone.now()-timedelta(seconds=1))
        self.assertIsNone(authenticate(username=user.username,password='Changed-test-passphrase-44'))
    @override_settings(DEBUG=False)
    def test_demo_creation_is_not_allowed_in_production(self):
        with self.assertRaises(CommandError):
            call_command('create_demo_accounts',stdout=StringIO())
    def test_profile_address_saved_for_reference_flow(self):
        ResidentProfile.objects.create(user=self.resident,mobile='09171112222')
        self.client.force_login(self.resident)
        self.client.post('/profile/',{'first_name':'Alex','last_name':'Cruz','middle_name':'Santos','address':'Zone 4, Barangay Central'})
        profile=ResidentProfile.objects.get(user=self.resident)
        self.assertEqual(profile.address,'Zone 4, Barangay Central')

    def test_added_document_updates_catalogue_counts(self):
        self.client.force_login(self.admin)
        response=self.client.post('/management/documents/new/',{'name':'Local Certification','group':'certifications','description':'A new resident service.','fee':'To confirm','processing_time':'To confirm','bookable':True,'requirements_text':'Resident identification'})
        self.assertRedirects(response,'/management/documents/')
        self.assertTrue(Document.objects.filter(slug='local-certification').exists())
        self.assertContains(self.client.get('/documents/'),'2 documents in 3 groups')
        self.assertContains(self.client.get('/'),'See all 2 documents')
