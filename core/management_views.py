from datetime import date, datetime, timedelta
from functools import wraps
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction, IntegrityError, OperationalError
from django.db.models.deletion import ProtectedError
from django.db.models import Count, Exists, F, OuterRef, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from .management_forms import AccountAccessForm, AccountEditorForm, AccountDeletionForm, DocumentEditorForm, ScheduleForm
from .models import AccountLifecycle, AdminActivity, AppointmentSlot, Booking, BookingEvent, Document, Requirement,DeskMessage,WalkInEvent,WalkIn
from . import account_services

def administrator(view):
    @wraps(view)
    @login_required
    @never_cache
    def wrapped(request, *args, **kwargs):
        if not request.user.is_active or not request.user.is_superuser:
            raise PermissionDenied('Administrator access is required.')
        return view(request, *args, **kwargs)
    return wrapped

def record(user, action):
    AdminActivity.objects.create(actor=user, action=action)

@administrator
def dashboard(request):
    today = timezone.localdate()
    day_bookings = Booking.objects.filter(date=today)
    next_slots = AppointmentSlot.objects.filter(starts_at__gt=timezone.now(), is_open=True)
    counts = {row['date']: row['total'] for row in Booking.objects.filter(date__gte=today-timedelta(days=6), date__lte=today).values('date').annotate(total=Count('pk'))}
    maximum = max(counts.values(), default=1) or 1
    week = [{'day': today-timedelta(days=n), 'count': counts.get(today-timedelta(days=n), 0), 'height': max(3, int(100*counts.get(today-timedelta(days=n), 0)/maximum))} for n in range(6, -1, -1)]
    return render(request, 'management/dashboard.html', {
        'management_active': 'overview', 'today': today, 'total': day_bookings.count(),
        'walkin_total':WalkIn.objects.filter(date=today).count(),
        'arrived':day_bookings.filter(checked_in_at__isnull=False).count(),
        'waiting': day_bookings.filter(status__in=['confirmed', 'called', 'processing']).count(),
        'completed': day_bookings.filter(status='completed').count(),
        'residents': get_user_model().objects.filter(is_staff=False).exclude(account_lifecycle__deleted_at__isnull=False).count(),
        'document_count': Document.objects.count(), 'open_places': next_slots.aggregate(total=Sum(F('capacity')-F('reserved')))['total'] or 0,
        'appointments': day_bookings.select_related('resident', 'slot').prefetch_related('documents').order_by('slot__starts_at')[:8],
        'activity': AdminActivity.objects.select_related('actor')[:6], 'week': week,
    })

@administrator
def schedule(request):
    from .operations_forms import PublishForm
    from .scheduling import occurrences,publish
    today = timezone.localdate()
    form = PublishForm(request.POST or None, initial={'start_date': today+timedelta(days=1), 'end_date': today+timedelta(days=7)})
    preview=None
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        moments=list(occurrences(data))
        preview={'total':len(moments),'first':moments[:8]}
        if request.POST.get('action')!='preview':
            with transaction.atomic():
                result=publish(data)
                record(request.user, f'Published {result["created"]} appointment slots; preserved {result["existing"]} existing slots.')
            messages.success(request, f'Published {result["created"]} time slots. {result["existing"]} existing slots preserved; {result["blocked"]} closures skipped.')
            return redirect('management_schedule')
    try:
        selected = date.fromisoformat(request.GET.get('date', ''))
    except ValueError:
        selected = today
    slots = AppointmentSlot.objects.filter(starts_at__date=selected)
    return render(request, 'management/schedule.html', {'management_active': 'schedule', 'form': form, 'slots': slots, 'selected': selected,'preview':preview})

@administrator
@require_POST
@transaction.atomic
def slot_update(request, pk):
    slot = get_object_or_404(AppointmentSlot.objects.select_for_update(), pk=pk)
    if slot.starts_at <= timezone.now():
        messages.error(request, 'Past appointment slots cannot be changed.')
    else:
        action = request.POST.get('action')
        if action == 'toggle':
            slot.is_open = not slot.is_open
            slot.save(update_fields=['is_open'])
            record(request.user, f'{"Opened" if slot.is_open else "Closed"} appointment slot {slot}. Existing bookings retained.')
            messages.success(request, 'Appointment availability updated. Existing bookings are retained.')
        elif action == 'capacity':
            try:
                capacity = int(request.POST.get('capacity', ''))
            except ValueError:
                capacity = 0
            if capacity < max(1, slot.reserved) or capacity > 50:
                messages.error(request, f'Capacity must be between {max(1, slot.reserved)} and 50, and cannot be below existing reservations.')
            else:
                slot.capacity = capacity
                slot.save(update_fields=['capacity'])
                record(request.user, f'Changed capacity for {slot} to {capacity}.')
                messages.success(request, 'Slot capacity updated.')
        else:
            messages.error(request, 'Choose a valid availability action.')
    from django.urls import reverse
    return redirect(reverse('management_schedule')+'?date='+timezone.localtime(slot.starts_at).date().isoformat())

@administrator
def documents(request):
    query = request.GET.get('q', '').strip()[:150]
    items = Document.objects.annotate(requirement_count=Count('requirements'))
    if query:
        items = items.filter(Q(name__icontains=query)|Q(description__icontains=query))
    return render(request, 'management/documents.html', {'management_active': 'documents', 'documents': items, 'query': query})

@administrator
def document_edit(request, pk=None):
    doc = get_object_or_404(Document, pk=pk) if pk else Document()
    form = DocumentEditorForm(request.POST or None, instance=doc)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            saved = form.save(commit=False)
            if not saved.pk:
                saved.slug = slugify(saved.name)
                saved.position = Document.objects.count()
            saved.save()
            lines = form.cleaned_data['requirements_text']
            verified = form.cleaned_data['requirements_verified']
            current = list(saved.requirements.values_list('text', 'confirmed'))
            if current != [(line, verified) for line in lines]:
                saved.requirements.all().delete()
                Requirement.objects.bulk_create([Requirement(document=saved, text=line, confirmed=verified, position=i) for i, line in enumerate(lines)])
            record(request.user, f'Updated document and requirements: {saved.name}.')
        messages.success(request, 'Document details and requirements are now updated for residents.')
        return redirect('management_documents')
    return render(request, 'management/document_edit.html', {'management_active': 'documents', 'form': form, 'document': doc})

@administrator
def accounts(request):
    query = request.GET.get('q', '').strip()[:100]
    status = request.GET.get('status','current')
    role = request.GET.get('role','')
    if status not in ['current','active','inactive','deleted']:
        status='current'
    if role not in ['','resident','staff','admin']:
        role=''
    users = get_user_model().objects.select_related('resident_profile','account_lifecycle').order_by('-date_joined','-pk')
    if status=='deleted':
        users=users.filter(account_lifecycle__deleted_at__isnull=False)
    else:
        users=users.exclude(account_lifecycle__deleted_at__isnull=False)
        if status in ['active','inactive']:
            users=users.filter(is_active=status=='active')
    if role=='admin':
        users=users.filter(is_superuser=True)
    elif role=='staff':
        users=users.filter(is_staff=True,is_superuser=False)
    elif role=='resident':
        users=users.filter(is_staff=False,is_superuser=False)
    if query:
        users = users.filter(Q(first_name__icontains=query)|Q(last_name__icontains=query)|Q(email__icontains=query)|Q(username__icontains=query)|Q(resident_profile__mobile__icontains=query))
    users=users.annotate(booking_history=Exists(Booking.objects.filter(resident_id=OuterRef('pk'))),
                         service_history=Exists(BookingEvent.objects.filter(actor_id=OuterRef('pk'))),
                         administration_history=Exists(AdminActivity.objects.filter(actor_id=OuterRef('pk'))),
                         message_history=Exists(DeskMessage.objects.filter(sender_id=OuterRef('pk'))),
                         walkin_history=Exists(WalkInEvent.objects.filter(actor_id=OuterRef('pk'))))
    page=Paginator(users,25).get_page(request.GET.get('page'))
    for user in page.object_list:
        user.can_purge=not (user.booking_history or user.service_history or user.administration_history or user.message_history or user.walkin_history)
    return render(request, 'management/accounts.html', {'management_active':'accounts','accounts':page.object_list,'page':page,'query':query,'account_status':status,'account_role':role})

@administrator
@require_POST
def account_update(request, pk):
    user = get_object_or_404(get_user_model(), pk=pk)
    if user.is_superuser or user.pk == request.user.pk:
        raise PermissionDenied('Administrator accounts must be managed through the protected Django administration site.')
    form = AccountAccessForm(request.POST)
    if form.is_valid():
        try:
            account_services.update_access(request.user,pk,form.cleaned_data['role'],form.cleaned_data['active'])
        except ValidationError as exc:
            messages.error(request,' '.join(exc.messages))
        except (IntegrityError,OperationalError):
            messages.error(request,'The account changed during this request. Refresh and try again.')
        else:
            messages.success(request,'Account access updated. Existing sessions were revoked if access changed.')
    else:
        messages.error(request, 'Choose a valid role and account state.')
    return redirect('management_accounts')

@administrator
@require_http_methods(['GET','POST'])
def account_edit(request,pk):
    user=get_object_or_404(get_user_model().objects.select_related('resident_profile','account_lifecycle'),pk=pk)
    if account_services.is_deleted(user):
        messages.error(request,'Restore the deleted account before editing its details.')
        return redirect('management_accounts')
    form=AccountEditorForm(request.POST if request.method=='POST' else None,user=user)
    if request.method=='POST' and form.is_valid():
        try:
            updated=account_services.edit_account(request.user,pk,form.cleaned_data,keep_session=request.session.session_key)
        except IntegrityError:
            form.add_error(None,'An email, login or mobile number was just claimed by another account. Please use different details.')
        except OperationalError:
            form.add_error(None,'The account changed during this request. Refresh and try again.')
        except ValidationError as exc:
            form.add_error(None,exc)
        else:
            if updated.pk==request.user.pk and form.cleaned_data.get('new_password'):
                update_session_auth_hash(request,updated)
            messages.success(request,'Account details and access have been saved.')
            return redirect('management_account_edit',pk=pk)
    return render(request,'management/account_edit.html',{'management_active':'accounts','account':user,'form':form,'booking_count':user.bookings.count()})

@administrator
@require_http_methods(['GET','POST'])
def account_delete(request,pk):
    user=get_object_or_404(get_user_model(),pk=pk)
    if user.is_superuser or user.pk==request.user.pk:
        raise PermissionDenied('Administrator accounts cannot be deleted here.')
    history=account_services.has_history(user)
    deleted=account_services.is_deleted(user)
    form=AccountDeletionForm(request.POST if request.method=='POST' else None,user=user,can_purge=not history)
    if request.method=='POST' and form.is_valid():
        try:
            account_services.delete_account(request.user,pk,form.cleaned_data['mode'])
        except ValidationError as exc:
            form.add_error(None,exc)
        except (ProtectedError,IntegrityError,OperationalError):
            form.add_error(None,'The account or its booking history changed. Refresh this page before continuing.')
        else:
            messages.success(request,'Account permanently deleted.' if form.cleaned_data['mode']=='permanent' else 'Account deleted. History was retained and pending bookings were cancelled.')
            return redirect('management_accounts')
    return render(request,'management/account_delete.html',{'management_active':'accounts','account':user,'form':form,'has_history':history,'is_deleted':deleted,'booking_count':user.bookings.count(),'pending_count':user.bookings.filter(status='confirmed').count()})

@administrator
@require_POST
def account_restore(request,pk):
    get_object_or_404(get_user_model(),pk=pk)
    try:
        user=account_services.restore_account(request.user,pk)
    except ValidationError as exc:
        messages.error(request,' '.join(exc.messages))
        return redirect('management_accounts')
    messages.success(request,'Account restored as inactive. Review its details and enable sign-in when ready. Cancelled bookings were not restored.')
    return redirect('management_account_edit',pk=user.pk)

@administrator
def activity(request):
    return render(request, 'management/activity.html', {'management_active': 'activity', 'activity': AdminActivity.objects.select_related('actor')[:100], 'events': BookingEvent.objects.select_related('actor', 'booking')[:50]})
