import csv
import hashlib
import io
import uuid
from datetime import date,datetime,timedelta
from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied,ValidationError
from django.db import transaction,IntegrityError,OperationalError
from django.http import Http404,HttpResponse,JsonResponse
from django.shortcuts import get_object_or_404,redirect,render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST,require_http_methods
from .management_views import administrator,record
from .models import AppointmentSlot,Booking,DeskMessage,Document,Notification,OpeningHours,ScheduleException,WalkIn
from .operations_forms import CheckInForm,ExceptionForm,MessageForm,OpeningHoursForm,PublishForm,ReportFilterForm,SlotEditorForm,WalkInForm
from . import queue_services as queue
from . import scheduling

def staff_member(view):
    @wraps(view)
    @login_required
    @never_cache
    def wrapped(request,*args,**kwargs):
        queue.staff_only(request.user)
        return view(request,*args,**kwargs)
    return wrapped

def _day(request):
    try:
        return date.fromisoformat(request.GET.get('date',''))
    except ValueError:
        return timezone.localdate()

def desk_data(day):
    booked=Booking.objects.filter(date=day).select_related('resident','resident__resident_profile','slot').prefetch_related('documents')
    walkins=queue.priority_queue(WalkIn.objects.filter(date=day).prefetch_related('documents'))
    booked_waiting=booked.filter(status='confirmed',checked_in_at__isnull=False).order_by('slot__starts_at','queue_number')
    walkin_waiting=walkins.filter(status='waiting')
    now_booked=booked.filter(status__in=['called','processing']).order_by('called_at').first()
    now_walkin=walkins.filter(status__in=['called','processing']).order_by('called_at').first()
    unread=DeskMessage.objects.filter(read_by_staff=False,sender__is_staff=False).count()
    return {'booked':booked.order_by('slot__starts_at','queue_number'),'walkins':walkins,'waiting_booked':booked_waiting,'waiting_walkins':walkin_waiting,
            'now_booked':now_booked,'now_walkin':now_walkin,'count_booked':booked_waiting.count(),'count_walkin':walkin_waiting.count(),
            'unread_messages':unread,'completed_count':booked.filter(status='completed').count()+walkins.filter(status='completed').count(),
            'not_arrived':booked.filter(status='confirmed',checked_in_at__isnull=True).count()}

@staff_member
def staff_desk(request):
    day=_day(request)
    data=desk_data(day)
    data.update(day=day,is_today=day==timezone.localdate(),staff_active='queue',form=MessageForm())
    return render(request,'staff/desk.html',data)

@staff_member
def desk_snapshot(request):
    data=desk_data(_day(request))
    return JsonResponse({'booked':data['count_booked'],'walkin':data['count_walkin'],'completed':data['completed_count'],'messages':data['unread_messages'],
                         'current_booked':str(data['now_booked'].pk) if data['now_booked'] else '',
                         'current_walkin':str(data['now_walkin'].pk) if data['now_walkin'] else ''})

@staff_member
@require_POST
def call_next(request):
    try:
        entry=queue.call_next(request.user,request.POST.get('lane',''))
    except (ValidationError,IntegrityError,OperationalError) as exc:
        messages.error(request,' '.join(exc.messages) if isinstance(exc,ValidationError) else 'The queue changed. Please refresh and call again.')
    else:
        messages.success(request,f'{entry.ticket} is now being called.')
    return redirect('staff')

@staff_member
@require_POST
def recall(request,lane,pk):
    if lane=='booked':
        pk=_booking_id(pk)
        get_object_or_404(Booking,pk=pk)
    elif lane=='walkin':
        try:
            pk=int(pk)
        except ValueError:
            raise Http404
        get_object_or_404(WalkIn,pk=pk)
    else:
        raise Http404
    from django.core.cache import cache
    key=f'recall:{lane}:{pk}'
    try:
        if not cache.add(key,True,10):
            raise ValidationError('This number was just called. Wait a few seconds before calling again.')
        queue.recall(request.user,lane,pk)
    except ValidationError as exc:
        messages.error(request,' '.join(exc.messages))
    else:
        messages.success(request,'The queue number was called again.')
    return redirect('staff')

def _booking_id(value):
    try:
        return uuid.UUID(str(value))
    except (ValueError,TypeError):
        raise Http404

@staff_member
@require_http_methods(['GET','POST'])
def staff_messages(request):
    search=request.GET.get('q','').strip()[:100]
    candidates=Booking.objects.filter(resident__is_active=True).exclude(resident__account_lifecycle__deleted_at__isnull=False).select_related('resident','slot').prefetch_related('documents').order_by('-created_at')
    if search:
        from django.db.models import Q
        candidates=candidates.filter(Q(resident__first_name__icontains=search)|Q(resident__last_name__icontains=search)|Q(resident__email__icontains=search))
    selected=request.GET.get('booking') or request.POST.get('booking')
    booking=get_object_or_404(candidates,pk=_booking_id(selected)) if selected else candidates.first()
    form=MessageForm(request.POST if request.method=='POST' else None)
    if request.method=='POST':
        if not booking:
            raise Http404
        if form.is_valid():
            try:
                queue.send_message(request.user,booking,form.cleaned_data['body'])
            except ValidationError as exc:
                form.add_error('body',exc)
            else:
                messages.success(request,'Message sent to the resident’s in-app inbox.')
                return redirect(reverse('staff_messages')+'?booking='+str(booking.pk))
    thread=[]
    if booking:
        booking.messages.filter(read_by_staff=False).update(read_by_staff=True)
        thread=booking.messages.select_related('sender')
    return render(request,'staff/messages.html',{'staff_active':'messages','conversations':candidates[:100],'booking':booking,'thread':thread,'form':form,'search':search})

@login_required
@never_cache
@require_http_methods(['GET','POST'])
def resident_messages(request,pk):
    booking=get_object_or_404(Booking.objects.select_related('resident','slot'),pk=pk,resident=request.user)
    form=MessageForm(request.POST if request.method=='POST' else None)
    if request.method=='POST' and form.is_valid():
        queue.send_message(request.user,booking,form.cleaned_data['body'])
        return redirect('resident_messages',pk=pk)
    booking.messages.filter(read_by_resident=False).update(read_by_resident=True)
    return render(request,'resident/messages.html',{'booking':booking,'thread':booking.messages.select_related('sender'),'form':form,'resident_active':'notifications'})

@login_required
@never_cache
def ticket_qr(request,pk):
    booking=get_object_or_404(Booking,pk=pk,resident=request.user)
    import qrcode
    import qrcode.image.svg
    url=request.build_absolute_uri(reverse('management_checkin')+'?ticket='+queue.ticket_token(booking))
    qr=qrcode.make(url,image_factory=qrcode.image.svg.SvgPathImage,box_size=6,border=4)
    output=io.BytesIO()
    qr.save(output)
    return HttpResponse(output.getvalue(),content_type='image/svg+xml')

@administrator
@require_http_methods(['GET','POST'])
def checkin(request):
    form=CheckInForm(request.POST if request.method=='POST' else None,initial={'ticket':request.GET.get('ticket','')})
    booking=None
    raw=request.GET.get('ticket','') if request.method=='GET' else ''
    if request.method=='POST' and form.is_valid():
        raw=form.cleaned_data['ticket']
    if raw:
        try:
            booking=queue.resolve_ticket(raw)
            if request.method=='POST' and request.POST.get('action')=='confirm':
                booking,created=queue.check_in(request.user,booking.pk)
                messages.success(request,'Arrival recorded. The resident is ready for Window 1.' if created else 'This resident has already checked in.')
                return redirect(reverse('management_checkin')+'?ticket='+queue.ticket_token(booking))
        except ValidationError as exc:
            form.add_error('ticket',exc)
    return render(request,'operations/checkin.html',{'management_active':'checkin','form':form,'booking':booking})

@administrator
@require_http_methods(['GET','POST'])
def walkins(request):
    form=WalkInForm(request.POST if request.method=='POST' else None)
    if request.method=='POST' and form.is_valid():
        entry=queue.register_walkin(request.user,form.cleaned_data)
        record(request.user,f'Registered {entry.ticket} at Window 2 ({entry.get_priority_display()}).')
        messages.success(request,f'Walk-in registered. Queue number: {entry.ticket}.')
        return redirect('management_walkins')
    return render(request,'operations/walkins.html',{'management_active':'queue','form':form,'walkins':queue.priority_queue(WalkIn.objects.filter(date=timezone.localdate()).prefetch_related('documents'))})

@administrator
def service_queue(request):
    day=_day(request)
    return render(request,'operations/service_queue.html',desk_data(day)|{'management_active':'queue','day':day})

@administrator
@require_POST
def service_transition(request,lane,pk):
    status=request.POST.get('status','')
    try:
        if lane=='booked':
            booking=get_object_or_404(Booking,pk=_booking_id(pk))
            from .services import staff_transition
            entry=staff_transition(request.user,booking.pk,status)
        elif lane=='walkin':
            try:
                key=int(pk)
            except ValueError:
                raise Http404
            get_object_or_404(WalkIn,pk=key)
            entry=queue.walkin_transition(request.user,key,status)
        else:
            raise Http404
    except ValidationError as exc:
        messages.error(request,' '.join(exc.messages))
        return redirect('management_queue')
    return redirect(reverse('management_queue')+'?date='+entry.date.isoformat())

@administrator
@require_http_methods(['GET','POST'])
def opening_hours(request):
    today=timezone.localdate()
    form=OpeningHoursForm(request.POST if request.method=='POST' else None,initial={'start_date':today+timedelta(days=1),'end_date':today+timedelta(days=30)})
    preview=None
    if request.method=='POST' and form.is_valid():
        data=form.cleaned_data
        moments=list(scheduling.occurrences(data))
        preview={'total':len(moments),'first':moments[:8]}
        if request.POST.get('action')=='publish':
            with transaction.atomic():
                rule=OpeningHours.objects.create(**{k:data[k] for k in ['name','start_date','end_date','weekdays','start_time','end_time','break_start','break_end','interval','capacity']})
                rule.documents.set(data['documents'])
                result=scheduling.publish(data)
                record(request.user,f'Created recurring hours: {rule.name}; published {result["created"]} new appointments.')
            messages.success(request,f'Recurring hours saved. {result["created"]} slots added, {result["existing"]} existing slots retained, {result["blocked"]} closures skipped.')
            return redirect('management_hours')
    return render(request,'operations/hours.html',{'management_active':'hours','form':form,'preview':preview,'rules':OpeningHours.objects.prefetch_related('documents')})

@administrator
@require_POST
def hours_toggle(request,pk):
    rule=get_object_or_404(OpeningHours,pk=pk)
    rule.active=not rule.active
    rule.save(update_fields=['active'])
    record(request.user,f'{"Enabled" if rule.active else "Paused"} recurring hours: {rule.name}.')
    messages.success(request,'Recurring publishing updated. Existing appointments are retained; use a closure to block already published times.')
    return redirect('management_hours')

@administrator
@require_http_methods(['GET','POST'])
def closures(request):
    form=ExceptionForm(request.POST if request.method=='POST' else None)
    preview=None
    if request.method=='POST' and form.is_valid():
        data=form.cleaned_data
        scope=set(data['documents'].values_list('pk',flat=True))
        items=Booking.objects.filter(status='confirmed',slot__starts_at__lt=data['ends_at'],slot__starts_at__gte=data['starts_at']-timedelta(hours=4)).select_related('slot','resident').prefetch_related('documents')
        preview=[b for b in items if b.slot.starts_at+timedelta(minutes=b.slot.duration_minutes)>data['starts_at'] and (not scope or scope.intersection(d.pk for d in b.documents.all()))]
        if request.POST.get('action')=='publish':
            with transaction.atomic():
                # Serialize the closure with new reservations on affected slots.
                list(AppointmentSlot.objects.select_for_update().filter(starts_at__lt=data['ends_at'],starts_at__gte=data['starts_at']-timedelta(hours=4)).order_by('pk'))
                exception=form.save(commit=False)
                exception.created_by=request.user
                exception.save()
                form.save_m2m()
                notified=scheduling.notify_exception(exception,request.user)
                record(request.user,f'Published calendar exception {exception.name}; notified {notified} affected residents.')
            messages.success(request,f'Calendar exception saved. {notified} affected residents received an in-app notice. Existing bookings were retained.')
            return redirect('management_closures')
    return render(request,'operations/closures.html',{'management_active':'closures','form':form,'preview':preview,'exceptions':ScheduleException.objects.prefetch_related('documents')[:50]})

@administrator
@require_POST
@transaction.atomic
def closure_toggle(request,pk):
    exception=get_object_or_404(ScheduleException.objects.select_for_update(),pk=pk)
    list(AppointmentSlot.objects.select_for_update().filter(starts_at__lt=exception.ends_at,starts_at__gte=exception.starts_at-timedelta(hours=4)).order_by('pk'))
    exception.active=not exception.active
    exception.save(update_fields=['active'])
    count=scheduling.notify_exception(exception,request.user,reopening=not exception.active)
    record(request.user,f'{"Reinstated" if exception.active else "Lifted"} closure {exception.name}; notified {count} affected residents.')
    messages.success(request,'Calendar exception updated and affected residents notified.')
    return redirect('management_closures')

@administrator
@require_http_methods(['GET','POST'])
def slot_edit(request,pk):
    slot=get_object_or_404(AppointmentSlot,pk=pk)
    form=SlotEditorForm(request.POST if request.method=='POST' else None,instance=slot)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            locked=AppointmentSlot.objects.select_for_update().get(pk=pk)
            allowed={doc.pk for doc in form.cleaned_data['documents']}
            existing=set(Document.objects.filter(booking__slot=locked,booking__status__in=['confirmed','called','processing']).values_list('pk',flat=True))
            if form.cleaned_data['capacity']<locked.reserved:
                form.add_error('capacity','New reservations were added. Refresh and try again.')
            elif allowed and not existing.issubset(allowed):
                form.add_error('documents','A new booking uses another service. Retain its service or choose all.')
            else:
                for field in ['capacity','duration_minutes','is_open']:
                    setattr(locked,field,form.cleaned_data[field])
                locked.save(update_fields=['capacity','duration_minutes','is_open'])
                locked.documents.set(form.cleaned_data['documents'])
                record(request.user,f'Updated services and capacity for {slot}.')
                messages.success(request,'Appointment time updated. Existing bookings were retained.')
                return redirect(reverse('management_schedule')+'?date='+timezone.localtime(slot.starts_at).date().isoformat())
    return render(request,'operations/slot_edit.html',{'management_active':'schedule','form':form,'slot':slot})

def _report_data(data):
    booked=Booking.objects.filter(date__range=[data['start'],data['end']]).select_related('resident','slot').prefetch_related('documents').order_by('date','queue_number')
    walkins=WalkIn.objects.filter(date__range=[data['start'],data['end']]).prefetch_related('documents').order_by('date','queue_number')
    if data.get('document'):
        booked=booked.filter(documents=data['document'])
        walkins=walkins.filter(documents=data['document'])
    rows=[]
    for lane,items in [('booked',booked if data.get('lane')!='walkin' else []),('walkin',walkins if data.get('lane')!='booked' else [])]:
        for item in items:
            wait=(item.called_at-item.checked_in_at).total_seconds()/60 if item.called_at and item.checked_in_at and item.called_at>=item.checked_in_at else None
            processing=(item.completed_at-item.processing_started_at).total_seconds()/60 if item.completed_at and item.processing_started_at and item.completed_at>=item.processing_started_at else None
            rows.append({'date':item.date,'lane':lane,'ticket':item.ticket,'name':item.resident.get_full_name() if lane=='booked' else item.name,'status':item.status,'status_label':item.get_status_display(),
                         'documents':list(item.documents.all()),'checked_in':item.checked_in_at,'called':item.called_at,'processing_started':item.processing_started_at,'completed':item.completed_at,'wait':round(wait,1) if wait is not None else None,'processing':round(processing,1) if processing is not None else None})
    rows.sort(key=lambda row:(row['date'],row['lane'],row['ticket']))
    waits=[r['wait'] for r in rows if r['wait'] is not None]
    durations=[r['processing'] for r in rows if r['processing'] is not None]
    demand={}
    for row in rows:
        for doc in row['documents']:
            demand[doc.name]=demand.get(doc.name,0)+1
    return {'rows':rows,'total':len(rows),'completed':sum(r['status']=='completed' for r in rows),'missed':sum(r['status']=='missed' for r in rows),
            'average_wait':round(sum(waits)/len(waits),1) if waits else None,'average_processing':round(sum(durations)/len(durations),1) if durations else None,
            'timed_waits':len(waits),'timed_services':len(durations),'demand':sorted(demand.items(),key=lambda pair:(-pair[1],pair[0]))}

@administrator
def reports(request):
    today=timezone.localdate()
    form=ReportFilterForm(request.GET or None,initial={'start':today-timedelta(days=6),'end':today,'lane':'all'})
    if not request.GET:
        form=ReportFilterForm({'start':today-timedelta(days=6),'end':today,'lane':'all'})
    report={}
    if form.is_valid():
        report=_report_data(form.cleaned_data)
        if request.GET.get('export')=='csv':
            response=HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition']='attachment; filename="dokyugo-service-report.csv"'
            writer=csv.writer(response)
            writer.writerow(['Date','Window','Ticket','Resident','Documents','Status','Checked in','First called','Processing started','Completed','Wait (minutes)','Processing (minutes)'])
            def safe(value):
                value=str(value)
                return "'"+value if value.lstrip().startswith(('=','+','-','@')) else value
            def stamp(value):
                return timezone.localtime(value).isoformat() if value else ''
            for row in report['rows']:
                writer.writerow([row['date'],row['lane'],row['ticket'],safe(row['name']),safe(', '.join(d.name for d in row['documents'])),row['status'],stamp(row['checked_in']),stamp(row['called']),stamp(row['processing_started']),stamp(row['completed']),row['wait'] if row['wait'] is not None else '',row['processing'] if row['processing'] is not None else ''])
            return response
    params=request.GET.copy()
    params['export']='csv'
    if not request.GET:
        params.update({'start':str(today-timedelta(days=6)),'end':str(today),'lane':'all'})
    return render(request,'operations/reports.html',report|{'management_active':'reports','form':form,'export_query':params.urlencode()})
