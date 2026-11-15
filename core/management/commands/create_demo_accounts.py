from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from core.models import ResidentProfile

ACCOUNTS = [
    ('admin@dokyugo.test', 'AdminDemo!2026', 'Admin', '09000000001', True, True),
    ('staff@dokyugo.test', 'StaffDemo!2026', 'Staff', '09000000002', True, False),
    ('user@dokyugo.test', 'UserDemo!2026', 'Resident', '09000000003', False, False),
]

class Command(BaseCommand):
    help = 'Create explicitly requested local test accounts with a 7-day expiry. Never runs automatically.'
    def add_arguments(self, parser):
        parser.add_argument('--reset-passwords', action='store_true', help='Reset only previously marked demo accounts and renew their expiry.')
        parser.add_argument('--disable', action='store_true', help='Deactivate these demo accounts without removing booking history.')
    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Demo accounts can only be managed with DJANGO_DEBUG=1.')
        User = get_user_model()
        for email, password, name, mobile, staff, admin in ACCOUNTS:
            user = User.objects.filter(username=email).first()
            # Account edits may have changed a demo login. Its original mobile
            # and explicit expiry marker still identify that seeded account.
            if not user:
                marked = ResidentProfile.objects.filter(mobile=mobile,demo_expires_at__isnull=False).select_related('user').first()
                if marked:
                    user=marked.user
            if user:
                profile = ResidentProfile.objects.filter(user=user).first()
                if not profile or profile.demo_expires_at is None:
                    raise CommandError(f'{email} already exists and is not a marked demo account. No account was changed.')
                if options['disable']:
                    user.is_active = False
                    user.save(update_fields=['is_active'])
                    self.stdout.write(f'Disabled {email}')
                    continue
                if not options['reset_passwords']:
                    self.stdout.write(f'Preserved existing demo account: {user.username}')
                    continue
            elif options['disable']:
                continue
            else:
                user = User(username=email, email=email, first_name=name, last_name='Demo')
                profile = ResidentProfile(user=user, mobile=mobile)
            user.is_staff, user.is_superuser, user.is_active = staff, admin, True
            user.username=user.email=email
            user.set_password(password)
            user.save()
            profile.user = user
            profile.demo_expires_at = timezone.now() + timedelta(days=7)
            profile.save()
            self.stdout.write(f'{name}: {email} | {password} | expires {timezone.localtime(profile.demo_expires_at):%b %d, %Y %I:%M %p}')
        self.stdout.write(self.style.SUCCESS('Local demo accounts ready. Login at /login/.'))
