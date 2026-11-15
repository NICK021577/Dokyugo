import csv
import io
import uuid
from datetime import datetime,time,timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.exceptions import PermissionDenied,ValidationError
from django.core.management import call_command
from django.test import TestCase,override_settings
from django.urls import reverse
from django.utils import timezone
from .models import AppointmentSlot,Booking,DeskMessage,Document,Notification,OpeningHours,ScheduleException,WalkIn
from .operations_forms import SlotEditorForm
from .operations_views import _report_data
from . import queue_services as queue,scheduling,services,account_services

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class OperationsTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.admin=User.objects.create_superuser('ops-admin',password='test',first_name='Admin')
        self.staff=User.objects.create_user('ops-staff',password='test',is_staff=True)
        self.resident=User.objects.create_user('ops-resident',password='test',first_name='Alex')
        self.other=User.objects.create_user('ops-other',password='test')
        self.doc=Document.objects.create(name='Clearance',slug='ops-clearance',group='clearances')
        self.doc2=Document.objects.create(name='Residency',slug='ops-residency',group='certificates')
        self.start=timezone.now()+timedelta(days=3)
        self.slot=AppointmentSlot.objects.create(starts_at=self.start,capacity=4)
        self.booking=services.book(self.resident,[self.doc],self.slot,uuid.uuid4())
    def arrive(self):
        with patch('core.queue_services.timezone.now',return_value=self.start-timedelta(minutes=10)),patch('core.queue_services.timezone.localdate',return_value=timezone.localtime(self.start).date()):
            return queue.check_in(self.admin,self.booking.pk)
    def walkin(self,priority='regular',name='Walk-in'):
        return queue.register_walkin(self.admin,{'name':name,'priority':priority,'documents':[self.doc]})
    def test_admin_pages_render_and_staff_cannot_manage(self):
        paths=['/management/queue/','/management/walk-ins/','/management/check-in/','/management/opening-hours/','/management/closures/','/management/reports/',f'/management/slots/{self.slot.pk}/edit/']
        self.walkin()
        for user,status in [(self.admin,200),(self.staff,403),(self.resident,403)]:
            self.client.force_login(user)
            for path in paths:
                with self.subTest(path=path,user=user.username):
                    self.assertEqual(self.client.get(path).status_code,status)
    def test_staff_can_only_call_and_message(self):
        services.staff_transition(self.staff,self.booking.pk,'called')
        with self.assertRaises(PermissionDenied):
            services.staff_transition(self.staff,self.booking.pk,'processing')
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(reverse('management_transition',args=['booked',self.booking.pk]),{'status':'completed'}).status_code,403)
        services.staff_transition(self.admin,self.booking.pk,'processing')
        result=services.staff_transition(self.admin,self.booking.pk,'completed')
        self.assertIsNotNone(result.completed_at)
        self.assertIsNotNone(result.processing_started_at)
    def test_walkin_numbers_priority_and_service_transitions(self):
        regular=self.walkin()
        senior=self.walkin('senior')
        pwd=self.walkin('pwd')
        self.assertEqual([regular.ticket,senior.ticket,pwd.ticket],['W-001','W-002','W-003'])
        self.assertEqual(queue.call_next(self.staff,'walkin').pk,senior.pk)
        with self.assertRaises(ValidationError): queue.call_next(self.staff,'walkin')
        with self.assertRaises(PermissionDenied): queue.walkin_transition(self.staff,senior.pk,'processing')
        queue.walkin_transition(self.admin,senior.pk,'processing')
        queue.walkin_transition(self.admin,senior.pk,'completed')
        self.assertEqual(queue.call_next(self.staff,'walkin').pk,pwd.pk)
        with self.assertRaises(PermissionDenied): queue.register_walkin(self.staff,{'name':'No','priority':'regular','documents':[self.doc]})
    def test_qr_is_signed_private_and_preview_does_not_check_in(self):
        token=queue.ticket_token(self.booking)
        self.assertEqual(queue.resolve_ticket('https://test/management/check-in/?ticket='+token).pk,self.booking.pk)
        for value in [token+'bad','invalid',signing.dumps({'booking':'invalid'},salt='dokyugo-arrival-v1')]:
            with self.assertRaises(ValidationError): queue.resolve_ticket(value)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('ticket_qr',args=[self.booking.pk])).status_code,404)
        self.client.force_login(self.resident)
        response=self.client.get(reverse('ticket_qr',args=[self.booking.pk]))
        self.assertEqual(response.status_code,200)
        self.assertIn(b'<svg',response.content)
        self.assertIn('no-store',response['Cache-Control'])
        self.client.force_login(self.admin)
        self.assertContains(self.client.get('/management/check-in/',{'ticket':token}),'Alex')
        self.booking.refresh_from_db()
        self.assertIsNone(self.booking.checked_in_at)
    def test_arrival_window_idempotence_and_expiry_protection(self):
        with self.assertRaises(ValidationError): queue.check_in(self.admin,self.booking.pk)
        with self.assertRaises(PermissionDenied): queue.check_in(self.staff,self.booking.pk)
        entry,created=self.arrive()
        self.assertTrue(created)
        self.assertIsNotNone(entry.checked_in_at)
        self.assertFalse(self.arrive()[1])
        with patch('core.management.commands.expire_bookings.timezone.now',return_value=self.start+timedelta(hours=2)):
            call_command('expire_bookings',stdout=io.StringIO())
        entry.refresh_from_db()
        self.assertEqual(entry.status,'confirmed')
    def test_late_arrivals_rejected(self):
        with patch('core.queue_services.timezone.now',return_value=self.start+timedelta(minutes=16)),patch('core.queue_services.timezone.localdate',return_value=timezone.localtime(self.start).date()):
            with self.assertRaises(ValidationError): queue.check_in(self.admin,self.booking.pk)
    def test_booked_call_next_requires_arrival_and_single_current(self):
        with self.assertRaises(ValidationError): queue.call_next(self.staff,'booked')
        self.arrive()
        with patch('core.queue_services.timezone.localdate',return_value=self.booking.date):
            self.assertEqual(queue.call_next(self.staff,'booked').pk,self.booking.pk)
            with self.assertRaises(ValidationError): queue.call_next(self.staff,'booked')
            queue.recall(self.staff,'booked',self.booking.pk)
    def test_messages_are_private_escaped_and_marked_read(self):
        with self.assertRaises(PermissionDenied): queue.send_message(self.other,self.booking,'No access')
        with self.assertRaises(ValidationError): queue.send_message(self.staff,self.booking,' ')
        queue.send_message(self.staff,self.booking,'<script>alert(1)</script>')
        self.assertTrue(Notification.objects.filter(booking=self.booking,text__startswith='Message from').exists())
        self.client.force_login(self.resident)
        response=self.client.get(reverse('resident_messages',args=[self.booking.pk]))
        self.assertContains(response,'&lt;script&gt;')
        self.assertNotContains(response,'<script>alert(1)</script>')
        self.assertTrue(self.booking.messages.get().read_by_resident)
        self.client.post(reverse('resident_messages',args=[self.booking.pk]),{'body':'Thank you'})
        self.client.force_login(self.staff)
        self.assertContains(self.client.get('/staff/messages/',{'booking':self.booking.pk}),'Thank you')
        self.assertFalse(self.booking.messages.filter(read_by_staff=False).exists())
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('resident_messages',args=[self.booking.pk])).status_code,404)
    def test_document_scopes_apply_to_calendar_and_booking(self):
        self.slot.documents.set([self.doc])
        self.client.force_login(self.other)
        response=self.client.get('/api/availability/',{'month':self.start.strftime('%Y-%m'),'documents':self.doc2.pk})
        slot=response.json()['days'][0]['slots'][0]
        self.assertFalse(slot['available'])
        self.assertEqual(slot['reason'],'Different service')
        with self.assertRaises(ValidationError): services.book(self.other,[self.doc2],self.slot,uuid.uuid4())
        self.assertEqual(self.client.get('/api/slots/',{'documents':self.doc2.pk}).json()['slots'],[])
        self.assertEqual(self.client.get('/api/availability/',{'documents':'bad'}).status_code,400)
    def test_closures_preserve_bookings_notify_and_block_new(self):
        exception=ScheduleException.objects.create(name='Holiday',kind='holiday',starts_at=self.start-timedelta(minutes=1),ends_at=self.start+timedelta(hours=1),created_by=self.admin)
        self.assertEqual(scheduling.notify_exception(exception,self.admin),1)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status,'confirmed')
        with self.assertRaises(ValidationError): services.book(self.other,[self.doc],self.slot,uuid.uuid4())
        self.assertEqual(self.client.get('/api/slots/').json()['slots'],[])
        exception.documents.set([self.doc2])
        self.assertEqual(scheduling.slot_reason(self.slot,[self.doc]),'')
        self.assertEqual(scheduling.notify_exception(exception,self.admin),0)
    def test_hours_skip_breaks_weekends_and_keep_reservations(self):
        day=timezone.localdate()+timedelta(days=7)
        data={'start_date':day,'end_date':day,'weekdays':[day.weekday()],'start_time':time(9),'end_time':time(12),'break_start':time(10),'break_end':time(11),'interval':30,'capacity':3,'documents':[self.doc]}
        result=scheduling.publish(data)
        self.assertEqual(result['created'],4)
        slots=AppointmentSlot.objects.filter(starts_at__date=day)
        self.assertEqual([timezone.localtime(s.starts_at).hour for s in slots],[9,9,11,11])
        self.assertEqual(slots.first().documents.get(),self.doc)
        data['capacity']=9
        self.assertEqual(scheduling.publish(data)['existing'],4)
        self.assertEqual(slots.first().capacity,3)
        data['weekdays']=[(day.weekday()+1)%7]
        self.assertEqual(list(scheduling.occurrences(data)),[])
    def test_recurring_publisher_and_paused_rules(self):
        day=timezone.localdate()+timedelta(days=2)
        rule=OpeningHours.objects.create(name='Week',start_date=day,end_date=day,weekdays=[day.weekday()],start_time=time(9),end_time=time(10),capacity=2)
        rule.documents.set([self.doc])
        call_command('publish_schedules',stdout=io.StringIO())
        self.assertEqual(AppointmentSlot.objects.filter(starts_at__date=day).count(),2)
        rule.active=False;rule.save()
        call_command('publish_schedules',stdout=io.StringIO())
        self.assertEqual(AppointmentSlot.objects.filter(starts_at__date=day).count(),2)
    def test_slot_editor_cannot_exclude_existing_booking(self):
        form=SlotEditorForm({'capacity':1,'duration_minutes':30,'is_open':True,'documents':[self.doc2.pk]},instance=self.slot)
        self.assertFalse(form.is_valid())
        self.assertIn('documents',form.errors)
        form=SlotEditorForm({'capacity':0,'duration_minutes':30},instance=self.slot)
        self.assertFalse(form.is_valid())
    def test_reports_use_real_timestamps_and_csv_is_safe(self):
        arrived=self.start
        Booking.objects.filter(pk=self.booking.pk).update(checked_in_at=arrived,called_at=arrived+timedelta(minutes=7),processing_started_at=arrived+timedelta(minutes=9),completed_at=arrived+timedelta(minutes=14),status='completed')
        walkin=self.walkin(name='=DANGEROUS()')
        data={'start':timezone.localdate(),'end':self.booking.date,'lane':'all'}
        report=_report_data(data)
        self.assertEqual(report['average_wait'],7)
        self.assertEqual(report['average_processing'],5)
        self.assertEqual(report['timed_waits'],1)
        self.assertEqual(report['total'],2)
        self.assertEqual(report['demand'],[('Clearance',2)])
        self.client.force_login(self.admin)
        response=self.client.get('/management/reports/',data|{'export':'csv'})
        rows=list(csv.reader(io.StringIO(response.content.decode())))
        self.assertTrue(any("'=DANGEROUS()" in row for row in rows))
        self.assertEqual(_report_data(data|{'lane':'booked'})['total'],1)
    def test_message_and_walkin_history_protect_authors(self):
        queue.send_message(self.staff,self.booking,'History')
        self.assertTrue(account_services.has_history(self.staff))
        walkin=self.walkin()
        queue.walkin_transition(self.staff,walkin.pk,'called')
        self.assertTrue(account_services.has_history(self.staff))
    def test_resident_bottom_nav_has_active_location(self):
        self.client.force_login(self.resident)
        for path,label in [('/resident/','Home'),('/bookings/','Bookings'),('/notifications/','Notifications'),('/profile/','Profile')]:
            response=self.client.get(path)
            self.assertContains(response,'aria-label="Resident navigation"')
            self.assertIn('aria-current="page"',response.content.decode().split('aria-label="Resident navigation"')[1])
    def test_closure_form_previews_then_saves_without_cancelling(self):
        self.client.force_login(self.admin)
        stamp=lambda dt:timezone.localtime(dt).strftime('%Y-%m-%dT%H:%M')
        payload={'name':'Office holiday','kind':'holiday','starts_at':stamp(self.start-timedelta(minutes=2)),'ends_at':stamp(self.start+timedelta(hours=1)),'action':'preview'}
        self.assertContains(self.client.post('/management/closures/',payload),'1 affected confirmed bookings')
        self.assertFalse(ScheduleException.objects.exists())
        response=self.client.post('/management/closures/',payload|{'action':'publish'})
        self.assertEqual(response.status_code,302)
        self.assertEqual(ScheduleException.objects.count(),1)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status,'confirmed')
        self.assertTrue(self.booking.notifications.filter(text__contains='Office holiday').exists())
    def test_recurring_form_preview_publish_and_validation(self):
        day=timezone.localdate()+timedelta(days=2)
        payload={'name':'Morning clearance','start_date':str(day),'end_date':str(day),'weekdays':[day.weekday()],'start_time':'09:00','end_time':'12:00','break_start':'10:00','break_end':'11:00','interval':30,'capacity':3,'documents':[self.doc.pk],'action':'preview'}
        self.client.force_login(self.admin)
        self.assertContains(self.client.post('/management/opening-hours/',payload),'4 candidate appointment times')
        self.assertFalse(OpeningHours.objects.exists())
        self.assertEqual(self.client.post('/management/opening-hours/',payload|{'action':'publish'}).status_code,302)
        self.assertEqual(OpeningHours.objects.count(),1)
        self.assertEqual(AppointmentSlot.objects.filter(starts_at__date=day).count(),4)
        # Invalid opening time alongside a valid break produces form errors, not a server error.
        self.assertEqual(self.client.post('/management/opening-hours/',payload|{'start_time':'bad'}).status_code,200)
    def test_slot_edit_preserves_reserved_count(self):
        self.client.force_login(self.admin)
        response=self.client.post(reverse('management_slot_edit',args=[self.slot.pk]),{'capacity':3,'duration_minutes':45,'is_open':True,'documents':[self.doc.pk]})
        self.assertEqual(response.status_code,302)
        self.slot.refresh_from_db()
        self.assertEqual((self.slot.reserved,self.slot.capacity,self.slot.duration_minutes),(1,3,45))
