import hashlib
import json
import uuid
from datetime import timedelta
from django import forms
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, OperationalError
from django.db.models import F, Q
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from .forms import BookingForm, LoginForm, ProfileForm, RegistrationForm, RescheduleForm, ResetForm
from .models import AppointmentSlot, Booking, Document
from . import services
from .availability import picker_context

def account_home(user):
    return 'management' if user.is_superuser else 'staff' if user.is_staff else 'resident'

def _slots():
    return AppointmentSlot.objects.filter(is_open=True, starts_at__gt=timezone.now(), reserved__lt=F('capacity'))

def home(request):
    featured = Document.objects.filter(slug__in=['barangay-clearance', 'barangay-business-clearance-business-permit', 'certificate-of-residency', 'certificate-of-indigency'])
    return render(request, 'public/home.html', {'featured': featured, 'document_count': Document.objects.count()})

def documents(request):
    query = request.GET.get('q', '').strip()[:150]
    docs = Document.objects.all()
    if query:
        docs = docs.filter(Q(name__icontains=query) | Q(description__icontains=query))
    groups = [{'key': key, 'label': label, 'documents': list(docs.filter(group=key))} for key, label in Document.Group.choices]
    subtitle = f'Choose a document to see exactly what to bring. {Document.objects.count()} documents in 3 groups.'
    return render(request, 'public/documents.html', {'groups': groups, 'query': query, 'count': docs.count(), 'active': 'documents', 'catalogue_subtitle': subtitle})

def document_detail(request, slug):
    doc = get_object_or_404(Document.objects.prefetch_related('requirements'), slug=slug)
    from .scheduling import slot_reason
    slots=[s for s in _slots().prefetch_related('documents')[:300] if not slot_reason(s,[doc])][:3]
    return render(request, 'public/document_detail.html', {'document': doc, 'slots': slots, 'others': Document.objects.filter(group=doc.group).exclude(pk=doc.pk)[:3], 'active': 'documents'})

def how_it_works(request):
    return render(request, 'public/how.html', {'active': 'how'})

def privacy(request):
    return render(request, 'public/privacy.html', {'active': 'privacy'})

def _rate_key(request, purpose):
    # No passwords or raw account identifiers are stored in throttle keys.
    identifier = request.POST.get('username', request.POST.get('identifier', '')).lower().strip()
    digest = hashlib.sha256((request.META.get('REMOTE_ADDR', '') + ':' + identifier).encode()).hexdigest()
    return f'{purpose}:{digest}'

@never_cache
def signup(request):
    if request.user.is_authenticated:
        return redirect('resident')
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            user = form.save()
        except IntegrityError:
            form.add_error(None, 'An account already uses these details. Please log in.')
        else:
            login(request, user, backend='core.auth.EmailOrMobileBackend')
            messages.success(request, 'Your account is active. You can now book your documents.')
            return redirect('resident')
    return render(request, 'accounts/signup.html', {'form': form, 'auth_kind': 'signup'})

@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect(account_home(request.user))
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        key = _rate_key(request, 'login')
        attempts = cache.get(key, 0)
        if attempts >= 10:
            form.add_error(None, 'Too many attempts. Please try again in 15 minutes.')
        elif form.is_valid():
            cache.delete(key)
            login(request, form.get_user())
            target = request.POST.get('next', request.GET.get('next', ''))
            if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(target)
            return redirect(account_home(request.user))
        else:
            cache.set(key, attempts + 1, 900)
    return render(request, 'accounts/login.html', {'form': form, 'auth_kind': 'login', 'next': request.GET.get('next', '')})

@require_POST
def logout_view(request):
    logout(request)
    return redirect('home')

@never_cache
def password_reset(request):
    form = ResetForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        key = _rate_key(request, 'reset')
        if cache.add(key, True, 60):
            form.save(request)
        return render(request, 'accounts/reset_done.html', {'auth_kind': 'reset'})
    return render(request, 'accounts/reset.html', {'form': form, 'auth_kind': 'reset'})

@login_required
def resident(request):
    upcoming = request.user.bookings.filter(status__in=['confirmed', 'called', 'processing'], slot__starts_at__gte=timezone.now()-timedelta(minutes=15)).select_related('slot').prefetch_related('documents').order_by('slot__starts_at')
    return render(request, 'resident/home.html', {'bookings': upcoming[:3], 'featured': Document.objects.all()[:4], 'resident_active': 'home'})

@login_required
def bookings(request):
    return render(request, 'resident/bookings.html', {'bookings': request.user.bookings.select_related('slot').prefetch_related('documents'), 'resident_active': 'bookings'})

@login_required
def book(request):
    initial = {'submission_key': uuid.uuid4()}
    if request.GET.get('document'):
        initial['documents'] = Document.objects.filter(slug=request.GET['document'], bookable=True).values_list('pk', flat=True)
    if request.GET.get('slot'):
        initial['slot'] = request.GET['slot']
    form = BookingForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        try:
            booking = services.book(request.user, **{key: form.cleaned_data[key] for key in ['documents', 'slot', 'submission_key']})
        except (ValidationError, IntegrityError, OperationalError) as exc:
            form.add_error(None, exc if isinstance(exc, ValidationError) else 'The appointment changed while you were booking. Please refresh and try another time.')
        else:
            messages.success(request, 'Booking confirmed. Save your ticket and arrive at your chosen time.')
            return redirect('ticket', pk=booking.pk)
    return render(request, 'resident/book.html', {'form': form, 'resident_active': 'bookings', 'picker': picker_context(form)})

@login_required
@never_cache
def ticket(request, pk):
    booking = get_object_or_404(Booking.objects.select_related('slot').prefetch_related('documents', 'events'), pk=pk, resident=request.user)
    return render(request, 'resident/ticket.html', {'booking': booking, 'resident_active': 'bookings'})

@login_required
@require_http_methods(['GET', 'POST'])
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking.objects.select_related('slot'), pk=pk, resident=request.user)
    if request.method == 'POST':
        try:
            services.cancel(request.user, pk)
        except ValidationError as exc:
            messages.error(request, ' '.join(exc.messages))
        else:
            messages.success(request, 'Your booking has been cancelled.')
        return redirect('ticket', pk=pk)
    return render(request, 'resident/cancel.html', {'booking': booking,'resident_active':'bookings'})

@login_required
def reschedule_booking(request, pk):
    booking = get_object_or_404(Booking.objects.select_related('slot'), pk=pk, resident=request.user)
    form = RescheduleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            services.reschedule(request.user, pk, form.cleaned_data['slot'])
        except (ValidationError, IntegrityError, OperationalError) as exc:
            form.add_error(None, exc if isinstance(exc, ValidationError) else 'The appointment is unavailable. Please refresh and try again.')
        else:
            messages.success(request, 'Your booking has been rescheduled.')
            return redirect('ticket', pk=pk)
    return render(request, 'resident/reschedule.html', {'form': form, 'booking': booking, 'picker': picker_context(form, booking),'resident_active':'bookings'})

@login_required
def notifications(request):
    if request.method == 'POST':
        request.user.notifications.filter(read=False).update(read=True)
        return redirect('notifications')
    return render(request, 'resident/notifications.html', {'notifications': request.user.notifications.select_related('booking'), 'resident_active': 'notifications'})

@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your personal information has been updated.')
        return redirect('profile')
    return render(request, 'resident/profile.html', {'form': form, 'resident_active': 'profile'})

@login_required
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Your password has been changed.')
        return redirect('profile')
    return render(request, 'resident/change_password.html', {'form': form,'resident_active':'profile'})

@user_passes_test(lambda u: u.is_active and u.is_staff)
@never_cache
def staff(request):
    from datetime import date
    try:
        day = date.fromisoformat(request.GET.get('date', ''))
    except ValueError:
        day = timezone.localdate()
    items = Booking.objects.filter(date=day).select_related('resident', 'slot').prefetch_related('documents').order_by('queue_number')
    return render(request, 'staff/queue.html', {'bookings': items, 'day': day, 'total': items.count(), 'waiting': items.filter(status='confirmed').count(), 'completed': items.filter(status='completed').count()})

@user_passes_test(lambda u: u.is_active and u.is_staff)
@require_POST
def staff_update(request, pk):
    get_object_or_404(Booking, pk=pk)
    try:
        services.staff_transition(request.user, pk, request.POST.get('status', ''))
    except ValidationError as exc:
        messages.error(request, ' '.join(exc.messages))
    else:
        messages.success(request, 'The queue has been updated.')
    from django.urls import reverse
    booking = Booking.objects.get(pk=pk)
    return redirect(reverse('staff')+'?date='+booking.date.isoformat())

def booking_json(booking):
    return {'id': str(booking.pk), 'queue_number': booking.ticket, 'status': booking.status,
            'status_label': booking.get_status_display(), 'starts_at': booking.slot.starts_at.isoformat(),
            'documents': [{'id': d.pk, 'name': d.name} for d in booking.documents.all()], 'can_change': booking.can_change,
            'checked_in_at':booking.checked_in_at.isoformat() if booking.checked_in_at else None}

@require_GET
def api_csrf(request):
    return JsonResponse({'csrfToken': get_token(request)})

@require_GET
def api_documents(request):
    return JsonResponse({'documents': [{'id': d.pk, 'name': d.name, 'slug': d.slug, 'group': d.group, 'description': d.description, 'bookable': d.bookable, 'fee': d.fee, 'processing_time': d.processing_time, 'requirements': list(d.requirements.values('id', 'text', 'confirmed'))} for d in Document.objects.prefetch_related('requirements')]})

@require_GET
def api_slots(request):
    from .scheduling import slot_reason
    slots = _slots().prefetch_related('documents')
    selected=[]
    if request.GET.get('documents'):
        try:
            selected=[int(value) for value in request.GET['documents'].split(',')]
            if len(selected)>30 or not selected or any(value<=0 for value in selected) or Document.objects.filter(pk__in=selected,bookable=True).count()!=len(set(selected)):
                raise ValueError
        except ValueError:
            return JsonResponse({'error':'Choose valid document IDs separated by commas.'},status=400)
    if request.GET.get('date'):
        from datetime import date
        try:
            day = date.fromisoformat(request.GET['date'])
        except ValueError:
            return JsonResponse({'error': 'Use a date in YYYY-MM-DD format.'}, status=400)
        slots = slots.filter(starts_at__date=day)
    return JsonResponse({'slots': [{'id': s.pk, 'starts_at': s.starts_at.isoformat(), 'remaining': s.remaining} for s in slots[:300] if not slot_reason(s,selected)]})

def _api_data(request):
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ValidationError('Send valid JSON.')
        if not isinstance(data, dict):
            raise ValidationError('Send a JSON object.')
        return data
    return request.POST

@never_cache
@require_http_methods(['GET', 'POST'])
def api_bookings(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please log in.'}, status=401)
    if request.method == 'GET':
        return JsonResponse({'bookings': [booking_json(b) for b in request.user.bookings.select_related('slot').prefetch_related('documents')[:100]]})
    try:
        data = _api_data(request)
        form = BookingForm(data)
        if not form.is_valid():
            return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
        booking = services.book(request.user, **{k: form.cleaned_data[k] for k in ['documents', 'slot', 'submission_key']})
    except ValidationError as exc:
        return JsonResponse({'errors': exc.messages}, status=400)
    except (IntegrityError, OperationalError):
        return JsonResponse({'error': 'The appointment changed. Please retry.'}, status=409)
    return JsonResponse(booking_json(booking), status=201)

@never_cache
@require_GET
def api_ticket(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please log in.'}, status=401)
    booking = get_object_or_404(Booking.objects.select_related('slot').prefetch_related('documents'), pk=pk, resident=request.user)
    return JsonResponse(booking_json(booking))

@require_POST
def api_booking_action(request, pk, action):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please log in.'}, status=401)
    get_object_or_404(Booking, pk=pk, resident=request.user)
    try:
        if action == 'cancel':
            booking = services.cancel(request.user, pk)
        elif action == 'reschedule':
            form = RescheduleForm(_api_data(request))
            if not form.is_valid():
                return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
            booking = services.reschedule(request.user, pk, form.cleaned_data['slot'])
        else:
            return JsonResponse({'error': 'Unknown action.'}, status=404)
    except ValidationError as exc:
        return JsonResponse({'errors': exc.messages}, status=400)
    except (IntegrityError, OperationalError):
        return JsonResponse({'error': 'The appointment changed. Please retry.'}, status=409)
    return JsonResponse(booking_json(booking))

@require_POST
def api_login(request):
    try:
        data = _api_data(request)
    except ValidationError as exc:
        return JsonResponse({'errors': exc.messages}, status=400)
    key = _rate_key(request, 'api-login')
    attempts = cache.get(key, 0)
    if attempts >= 10:
        return JsonResponse({'error': 'Too many attempts. Try again in 15 minutes.'}, status=429)
    form = LoginForm(request, data=data)
    if not form.is_valid():
        cache.set(key, attempts+1, 900)
        return JsonResponse({'error': 'Invalid mobile number/email or password.'}, status=400)
    cache.delete(key)
    login(request, form.get_user())
    return JsonResponse({'id': request.user.pk, 'name': request.user.get_full_name(), 'csrfToken': get_token(request)})

@require_POST
def api_logout(request):
    logout(request)
    return JsonResponse({'ok': True})

@never_cache
@require_GET
def api_me(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please log in.'}, status=401)
    return JsonResponse({'id': request.user.pk, 'name': request.user.get_full_name(), 'email': request.user.email, 'is_staff': request.user.is_staff})

@require_POST
def api_signup(request):
    try:
        data = _api_data(request)
    except ValidationError as exc:
        return JsonResponse({'errors': exc.messages}, status=400)
    form = RegistrationForm(data)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    try:
        user = form.save()
    except IntegrityError:
        return JsonResponse({'error': 'An account already uses these details.'}, status=409)
    login(request, user, backend='core.auth.EmailOrMobileBackend')
    return JsonResponse({'id': user.pk, 'name': user.get_full_name(), 'csrfToken': get_token(request)}, status=201)

@never_cache
@require_http_methods(['GET', 'POST'])
def api_notifications(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please log in.'}, status=401)
    if request.method == 'POST':
        request.user.notifications.filter(read=False).update(read=True)
        return JsonResponse({'ok': True})
    return JsonResponse({'notifications': [{'id': n.pk, 'booking_id': str(n.booking_id), 'text': n.text, 'read': n.read, 'created_at': n.created_at.isoformat()} for n in request.user.notifications.all()[:100]]})
