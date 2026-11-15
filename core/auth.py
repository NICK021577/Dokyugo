import re
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.utils import timezone
from .models import AccountLifecycle, ResidentProfile

def normalize_mobile(value):
    value = re.sub(r'[\s()-]', '', value)
    if value.startswith('+63'):
        value = '0' + value[3:]
    return value

class EmailOrMobileBackend(ModelBackend):
    def user_can_authenticate(self, user):
        if not super().user_can_authenticate(user):
            return False
        if AccountLifecycle.objects.filter(user=user, deleted_at__isnull=False).exists():
            return False
        # This also applies when Django restores an existing login session.
        expiry = ResidentProfile.objects.filter(user=user).values_list('demo_expires_at', flat=True).first()
        return expiry is None or (settings.DEBUG and expiry > timezone.now())

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        User = get_user_model()
        try:
            user = User.objects.get(Q(username__iexact=username.strip()) | Q(resident_profile__mobile=normalize_mobile(username)))
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            User().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
