import uuid
from datetime import timedelta
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from . import account_services, services
from .models import AccountLifecycle, AdminActivity, AppointmentSlot, Booking, BookingEvent, Document, ResidentProfile

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'], EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AccountManagementTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.admin=User.objects.create_user('admin@example.test',email='admin@example.test',password='Admin-test-passphrase-47!',first_name='Admin',last_name='Tester',is_staff=True,is_superuser=True)
        self.user=User.objects.create_user('resident@example.test',email='resident@example.test',password='Resident-test-passphrase-48!',first_name='Alex',last_name='Cruz')
        self.staff=User.objects.create_user('staff@example.test',email='staff@example.test',password='Staff-test-passphrase-49!',first_name='Mia',last_name='Santos',is_staff=True)
        ResidentProfile.objects.create(user=self.user,mobile='09171234567',address='Original address')
        self.slot=AppointmentSlot.objects.create(starts_at=timezone.now()+timedelta(days=3),capacity=2)
        self.doc=Document.objects.create(name='Clearance',slug='clearance',group='clearances',description='Local clearance')
        self.client.force_login(self.admin)
    def payload(self,**overrides):
        data={'first_name':'Alexandra','last_name':'Cruz','middle_name':'Diaz','email':'new@example.test','mobile':'+63 917 123 4567','address':'Zone 2, Central','role':'resident','active':'on','new_password':'','confirm_password':''}
        data.update(overrides)
        return data
    def url(self,action,user=None):
        return reverse('management_account_'+action,args=[(user or self.user).pk])
    def booking(self):
        return services.book(self.user,[self.doc],self.slot,uuid.uuid4())
    def deletion_payload(self,mode='archive'):
        return {'mode':mode,'confirmation':self.user.email,'acknowledge':'on'}
    def test_edit_details_updates_email_login_and_mobile(self):
        response=self.client.post(self.url('edit'),self.payload())
        self.assertRedirects(response,self.url('edit'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username,'new@example.test')
        self.assertEqual(self.user.first_name,'Alexandra')
        self.assertTrue(self.user.check_password('Resident-test-passphrase-48!'))
        profile=self.user.resident_profile
        self.assertEqual(profile.mobile,'09171234567')
        self.assertEqual(profile.address,'Zone 2, Central')
        self.assertIsNotNone(authenticate(username='new@example.test',password='Resident-test-passphrase-48!'))
        self.assertIsNone(authenticate(username='resident@example.test',password='Resident-test-passphrase-48!'))
    def test_duplicates_and_invalid_password_do_not_partially_save(self):
        for changes,error in [({'email':self.staff.email},'already uses this email'),({'mobile':'abc'},'11-digit'),({'new_password':'12345678','confirm_password':'12345678'},'password'),({'new_password':'Strong-passphrase-88!','confirm_password':'different'},'do not match')]:
            response=self.client.post(self.url('edit'),self.payload(**changes))
            self.assertEqual(response.status_code,200)
            self.assertContains(response,error)
            self.user.refresh_from_db()
            self.assertEqual(self.user.username,'resident@example.test')
    def test_duplicate_phone_is_rejected(self):
        ResidentProfile.objects.create(user=self.staff,mobile='09179998888')
        response=self.client.post(self.url('edit'),self.payload(mobile='09179998888'))
        self.assertContains(response,'already uses this mobile')
    def test_reset_password_revokes_sessions(self):
        other=Client()
        other.force_login(self.user)
        response=self.client.post(self.url('edit'),self.payload(new_password='Brand-new-passphrase-71!',confirm_password='Brand-new-passphrase-71!'))
        self.assertEqual(response.status_code,302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Brand-new-passphrase-71!'))
        self.assertEqual(other.get('/api/me/').status_code,401)
    def test_access_changes_revoke_session_and_cannot_grant_admin(self):
        other=Client()
        other.force_login(self.user)
        self.client.post(reverse('management_account',args=[self.user.pk]),{'role':'staff','active':'on'})
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_staff)
        self.assertEqual(other.get('/api/me/').status_code,401)
        other.force_login(self.user)
        self.client.post(reverse('management_account',args=[self.user.pk]),{'role':'resident'})
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.client.post(reverse('management_account',args=[self.user.pk]),{'role':'admin','active':'on'})
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_superuser)
    def test_archive_cancels_pending_booking_releases_capacity_and_retains_history(self):
        booking=self.booking()
        other=Client()
        other.force_login(self.user)
        response=self.client.post(self.url('delete'),self.deletion_payload())
        self.assertRedirects(response,'/management/accounts/')
        self.user.refresh_from_db()
        booking.refresh_from_db()
        self.slot.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertEqual(booking.status,'cancelled')
        self.assertEqual(self.slot.reserved,0)
        self.assertTrue(AccountLifecycle.objects.filter(user=self.user,deleted_at__isnull=False).exists())
        self.assertEqual(other.get('/api/me/').status_code,401)
        self.assertContains(self.client.get('/management/accounts/?status=deleted'),self.user.email)
        self.assertNotContains(self.client.get('/management/accounts/'),self.user.email)
        self.assertEqual(booking.events.count(),2)
    def test_confirmation_and_post_are_required(self):
        self.assertEqual(self.client.get(self.url('delete')).status_code,200)
        self.assertFalse(AccountLifecycle.objects.exists())
        response=self.client.post(self.url('delete'),{'mode':'archive','confirmation':'wrong','acknowledge':'on'})
        self.assertContains(response,'does not match')
        response=self.client.post(self.url('delete'),{'mode':'archive','confirmation':self.user.email})
        self.assertEqual(response.status_code,200)
        self.assertFalse(AccountLifecycle.objects.exists())
    def test_permanent_delete_unused_account(self):
        pk=self.user.pk
        response=self.client.post(self.url('delete'),self.deletion_payload('permanent'))
        self.assertRedirects(response,'/management/accounts/')
        self.assertFalse(get_user_model().objects.filter(pk=pk).exists())
        self.assertFalse(ResidentProfile.objects.filter(user_id=pk).exists())
        self.assertTrue(AdminActivity.objects.filter(action__contains=f'#{pk}').exists())
    def test_hard_delete_cannot_remove_booking_or_staff_activity_history(self):
        booking=self.booking()
        with self.assertRaises(ValidationError):
            account_services.delete_account(self.admin,self.user.pk,'permanent')
        BookingEvent.objects.create(booking=booking,actor=self.staff,description='Staff processed a document.')
        with self.assertRaises(ValidationError):
            account_services.delete_account(self.admin,self.staff.pk,'permanent')
        self.assertTrue(Booking.objects.filter(pk=booking.pk).exists())
    def test_archive_blocked_during_active_service(self):
        booking=self.booking()
        services.staff_transition(self.admin,booking.pk,'called')
        response=self.client.post(self.url('delete'),self.deletion_payload())
        self.assertContains(response,'Finish the account')
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertFalse(AccountLifecycle.objects.exists())
    def test_restore_is_inactive_and_cannot_undo_booking_cancellations(self):
        booking=self.booking()
        account_services.delete_account(self.admin,self.user.pk,'archive')
        response=self.client.post(self.url('restore'))
        self.assertRedirects(response,self.url('edit'))
        self.user.refresh_from_db()
        booking.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertEqual(booking.status,'cancelled')
        self.assertFalse(account_services.is_deleted(self.user))
        self.client.post(self.url('edit'),self.payload())
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
    def test_deleted_account_cannot_be_reenabled_without_restoring(self):
        account_services.delete_account(self.admin,self.user.pk,'archive')
        self.client.post(reverse('management_account',args=[self.user.pk]),{'role':'staff','active':'on'})
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        # Even an external accidental reactivation cannot bypass the deletion marker.
        get_user_model().objects.filter(pk=self.user.pk).update(is_active=True)
        self.assertIsNone(authenticate(username=self.user.username,password='Resident-test-passphrase-48!'))
    def test_administrator_can_edit_own_identity_without_losing_admin_or_session(self):
        response=self.client.post(self.url('edit',self.admin),self.payload(email='renamed-admin@example.test',mobile='',middle_name='',address='',role='resident',active='',new_password='New-admin-passphrase-92!',confirm_password='New-admin-passphrase-92!'))
        self.assertEqual(response.status_code,302)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_superuser)
        self.assertTrue(self.admin.is_active)
        self.assertEqual(self.client.get('/management/').status_code,200)
        self.assertEqual(self.client.post(self.url('delete',self.admin),{'mode':'permanent','confirmation':self.admin.email,'acknowledge':'on'}).status_code,403)
    def test_staff_and_resident_cannot_mutate_or_view_account_management(self):
        for actor in [self.staff,self.user]:
            self.client.force_login(actor)
            for action in ['edit','delete','restore']:
                self.assertEqual(self.client.get(self.url(action)).status_code,403)
                self.assertEqual(self.client.post(self.url(action),self.payload()).status_code,403)
    def test_status_role_search_and_pagination(self):
        self.assertContains(self.client.get('/management/accounts/?role=staff'),self.staff.email)
        self.assertNotContains(self.client.get('/management/accounts/?role=staff'),self.user.email)
        self.assertContains(self.client.get('/management/accounts/?q=09171234567'),self.user.email)
        get_user_model().objects.bulk_create([get_user_model()(username=f'extra{i}@example.test',email=f'extra{i}@example.test') for i in range(26)])
        response=self.client.get('/management/accounts/?page=2')
        self.assertEqual(response.context['page'].number,2)
        self.assertContains(response,'Page 2 of 2')
    def test_account_mutations_require_csrf(self):
        client=Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(self.url('delete'),self.deletion_payload()).status_code,403)
        self.assertTrue(get_user_model().objects.filter(pk=self.user.pk).exists())

    @override_settings(DEBUG=True)
    def test_demo_command_recognizes_an_edited_demo_login(self):
        from django.core.management import call_command
        from io import StringIO
        call_command('create_demo_accounts',stdout=StringIO())
        demo=get_user_model().objects.get(username='user@dokyugo.test')
        demo.username=demo.email='edited-demo@example.test'
        demo.save()
        call_command('create_demo_accounts',stdout=StringIO())
        self.assertFalse(get_user_model().objects.filter(username='user@dokyugo.test').exists())
        self.assertEqual(get_user_model().objects.filter(resident_profile__mobile='09000000003').count(),1)
        call_command('create_demo_accounts',reset_passwords=True,stdout=StringIO())
        demo.refresh_from_db()
        self.assertEqual(demo.username,'user@dokyugo.test')
