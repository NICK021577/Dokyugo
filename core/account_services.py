"""Account mutations shared by full editors and quick access controls."""
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .models import AccountLifecycle, AdminActivity, AppointmentSlot, Booking, BookingEvent, ResidentProfile,DeskMessage,WalkInEvent

def _administrator(actor):
    if not actor.is_active or not actor.is_superuser:
        raise PermissionDenied('Administrator access is required.')

def is_deleted(user):
    return AccountLifecycle.objects.filter(user=user,deleted_at__isnull=False).exists()

def has_history(user):
    return (Booking.objects.filter(resident=user).exists() or BookingEvent.objects.filter(actor=user).exists()
            or AdminActivity.objects.filter(actor=user).exists() or DeskMessage.objects.filter(sender=user).exists() or WalkInEvent.objects.filter(actor=user).exists())

def revoke_sessions(user, keep=None):
    keys=[]
    for session in Session.objects.filter(expire_date__gt=timezone.now()).iterator():
        if session.pk != keep and str(session.get_decoded().get('_auth_user_id','')) == str(user.pk):
            keys.append(session.pk)
    if keys:
        Session.objects.filter(pk__in=keys).delete()

def _access(user, role, active):
    if is_deleted(user):
        raise ValidationError('Restore the deleted account before editing its access.')
    if user.is_superuser:
        if role != 'admin' or active != user.is_active:
            raise PermissionDenied('Administrator access is protected.')
        return False
    if role not in ['resident','staff']:
        raise ValidationError('Choose Resident or Staff access.')
    changed=(user.is_staff != (role=='staff') or user.is_active != active)
    user.is_staff, user.is_active = role=='staff', active
    return changed

@transaction.atomic
def update_access(actor, user_id, role, active):
    _administrator(actor)
    user=get_user_model().objects.select_for_update().get(pk=user_id)
    if user.is_superuser or user.pk==actor.pk:
        raise PermissionDenied('Administrator access is protected.')
    changed=_access(user,role,active)
    user.save(update_fields=['is_staff','is_active'])
    if changed:
        revoke_sessions(user)
    AdminActivity.objects.create(actor=actor,action=f'Updated access for account #{user.pk}: {role}, {"active" if active else "inactive"}.')
    return user

@transaction.atomic
def edit_account(actor, user_id, data, keep_session=None):
    _administrator(actor)
    user=get_user_model().objects.select_for_update().get(pk=user_id)
    changed=_access(user,data['role'],data['active'])
    user.first_name, user.last_name = data['first_name'],data['last_name']
    user.email = user.username = data['email']
    password_changed=bool(data.get('new_password'))
    if password_changed:
        user.set_password(data['new_password'])
    user.save()
    profile=ResidentProfile.objects.filter(user=user).first()
    if profile or data.get('mobile'):
        if not profile:
            profile=ResidentProfile(user=user)
        profile.mobile=data['mobile']
        profile.middle_name=data.get('middle_name','')
        profile.address=data.get('address','')
        profile.save()
    if changed or password_changed:
        revoke_sessions(user,keep=keep_session if user.pk==actor.pk else None)
    AdminActivity.objects.create(actor=actor,action=f'Edited account #{user.pk} details/access'+(' and reset its password.' if password_changed else '.'))
    return user

@transaction.atomic
def delete_account(actor, user_id, mode):
    _administrator(actor)
    user=get_user_model().objects.select_for_update().get(pk=user_id)
    if user.is_superuser or user.pk==actor.pk:
        raise PermissionDenied('Administrator accounts cannot be deleted here.')
    if mode not in ['archive','permanent']:
        raise ValidationError('Choose a valid deletion method.')
    if mode=='permanent':
        if has_history(user):
            raise ValidationError('This account has booking or activity history. Use deletion with history retention instead.')
        identifier=user.pk
        revoke_sessions(user)
        user.delete()
        AdminActivity.objects.create(actor=actor,action=f'Permanently deleted unused account #{identifier}.')
        return
    if is_deleted(user):
        raise ValidationError('This account is already deleted.')
    if user.bookings.filter(status__in=['called','processing']).exists():
        raise ValidationError('Finish the account’s active service before deleting it.')
    cancelled=0
    for booking in Booking.objects.select_for_update().filter(resident=user,status='confirmed'):
        booking.status='cancelled'
        booking.save(update_fields=['status','updated_at'])
        AppointmentSlot.objects.filter(pk=booking.slot_id,reserved__gt=0).update(reserved=F('reserved')-1)
        BookingEvent.objects.create(booking=booking,actor=actor,description='Booking cancelled because its account was deleted by an administrator.')
        cancelled+=1
    user.is_active=False
    user.save(update_fields=['is_active'])
    state,_=AccountLifecycle.objects.get_or_create(user=user)
    state.deleted_at, state.deleted_by = timezone.now(),actor
    state.save()
    revoke_sessions(user)
    AdminActivity.objects.create(actor=actor,action=f'Deleted account #{user.pk}; retained history and cancelled {cancelled} pending bookings.')

@transaction.atomic
def restore_account(actor,user_id):
    _administrator(actor)
    user=get_user_model().objects.select_for_update().get(pk=user_id)
    state=AccountLifecycle.objects.select_for_update().filter(user=user,deleted_at__isnull=False).first()
    if not state:
        raise ValidationError('This account is not deleted.')
    state.deleted_at=state.deleted_by=None
    state.save()
    user.is_active=False
    user.save(update_fields=['is_active'])
    revoke_sessions(user)
    AdminActivity.objects.create(actor=actor,action=f'Restored account #{user.pk} as inactive. Cancelled bookings remain cancelled.')
    return user
