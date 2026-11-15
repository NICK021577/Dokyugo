"""Desktop desk/admin and resident phone QA. Uses and removes only identified QA records."""
import os,sys,uuid,json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import AppointmentSlot,Booking,Document,WalkIn,ResidentProfile,AdminActivity,ScheduleException,OpeningHours
from core import services,queue_services as queue
from playwright.sync_api import sync_playwright,expect
BASE=os.getenv('DOKYUGO_TEST_URL','http://127.0.0.1:8000')
OUT=ROOT/'artifacts';OUT.mkdir(exist_ok=True)
POOL=ThreadPoolExecutor(max_workers=1)
def db(fn): return POOL.submit(fn).result()
def login(page,user,password):
    page.goto(BASE+'/login/')
    page.locator('#id_username').fill(user.username)
    page.locator('#id_password').fill(password)
    page.get_by_role('button',name='Log in',exact=True).click()
    page.wait_for_url(lambda url:'/login/' not in url)
def main():
    # Do not let call-next affect an unrelated live queue.
    assert not Booking.objects.filter(date=timezone.localdate(),status__in=['called','processing']).exists(),'A live service is in progress; run this script on a test database.'
    assert not Booking.objects.filter(date=timezone.localdate(),status='confirmed',checked_in_at__isnull=False).exists(),'Arrived residents are waiting; use a test database.'
    assert not WalkIn.objects.filter(date=timezone.localdate(),status__in=['waiting','called','processing']).exists(),'Walk-ins are waiting; use a test database.'
    token=uuid.uuid4().hex[:10];password=uuid.uuid4().hex+'aA!';User=get_user_model()
    admin=User.objects.create_superuser('qa-ops-admin-'+token+'@example.test',password=password,first_name='QA',last_name='Administrator')
    staff=User.objects.create_user('qa-ops-staff-'+token+'@example.test',password=password,is_staff=True,first_name='QA',last_name='Staff')
    resident=User.objects.create_user('qa-ops-user-'+token+'@example.test',password=password,first_name='QA',last_name='Resident')
    ids=[admin.pk,staff.pk,resident.pk]
    ResidentProfile.objects.create(user=resident,mobile='09'+str(int(uuid.uuid4().hex[:10],16))[-9:].zfill(9))
    doc=Document.objects.filter(bookable=True).first();assert doc
    slot=AppointmentSlot.objects.create(starts_at=timezone.now()+timedelta(minutes=2),capacity=1)
    booking=services.book(resident,[doc],slot,uuid.uuid4())
    qr_token=queue.ticket_token(booking)
    errors=[];checks=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
            ac=browser.new_context(viewport={'width':1440,'height':1000});sc=browser.new_context(viewport={'width':1440,'height':1000});rc=browser.new_context(viewport={'width':390,'height':844})
            a=ac.new_page();s=sc.new_page();r=rc.new_page()
            for page in [a,s,r]:page.on('pageerror',lambda error:errors.append(str(error)))
            login(a,admin,password);login(s,staff,password);login(r,resident,password)
            a.goto(BASE+'/management/check-in/?ticket='+qr_token)
            expect(a.get_by_role('heading',name=booking.ticket,exact=True)).to_be_visible()
            a.get_by_role('button',name='Confirm identity & record arrival').click()
            assert db(lambda:Booking.objects.get(pk=booking.pk).checked_in_at) is not None
            s.goto(BASE+'/staff/')
            s.get_by_role('button',name='Call next booked resident',exact=True).click()
            assert db(lambda:Booking.objects.get(pk=booking.pk).status)=='called'
            s.get_by_role('link',name='Message resident',exact=True).click()
            s.locator('#id_body').fill('Please bring your original identification.')
            s.get_by_role('button',name='Send message').click()
            r.goto(BASE+f'/bookings/{booking.pk}/messages/')
            expect(r.get_by_text('Please bring your original identification.',exact=True)).to_be_visible()
            r.locator('#id_body').fill('Thank you, I am at the hall.')
            r.get_by_role('button',name='Send message').click()
            s.reload()
            expect(s.get_by_text('Thank you, I am at the hall.',exact=True)).to_be_visible()
            assert s.goto(BASE+'/management/queue/').status==403
            # Admin-only service controls update the resident's same booking record.
            for status in ['processing','completed']:
                a.goto(BASE+'/management/queue/')
                row=a.get_by_role('row').filter(has_text=booking.ticket)
                row.locator('select[name=status]').select_option(status)
                row.get_by_role('button',name='Save',exact=True).click()
                assert db(lambda:Booking.objects.get(pk=booking.pk).status)==status
            for priority,name in [('regular','QA Regular '+token),('senior','QA Senior '+token)]:
                a.goto(BASE+'/management/walk-ins/')
                a.locator('#id_name').fill(name);a.locator('#id_priority').select_option(priority)
                a.locator('input[name=documents]').first.check()
                a.get_by_role('button',name='Register & issue number').click()
            senior=db(lambda:WalkIn.objects.get(name='QA Senior '+token))
            s.goto(BASE+'/staff/');s.get_by_role('button',name='Call next walk-in resident').click()
            assert db(lambda:WalkIn.objects.get(pk=senior.pk).status)=='called'
            for width in [1440,1280,1024]:
                a.set_viewport_size({'width':width,'height':1000});s.set_viewport_size({'width':width,'height':1000})
                for slug,path in [('overview','/management/'),('queue','/management/queue/'),('check-in','/management/check-in/?ticket='+qr_token),('walk-ins','/management/walk-ins/'),('hours','/management/opening-hours/'),('closures','/management/closures/'),('reports','/management/reports/')]:
                    response=a.goto(BASE+path,wait_until='networkidle');assert response.status==200,(path,response.status)
                    assert a.evaluate('document.documentElement.scrollWidth <= innerWidth'),(slug,width)
                    if width==1440:a.screenshot(path=str(OUT/f'ops-{slug}-1440.png'),full_page=True)
                    checks.append((slug,width))
                for slug,path in [('staff','/staff/'),('inbox','/staff/messages/?booking='+str(booking.pk))]:
                    assert s.goto(BASE+path,wait_until='networkidle').status==200
                    assert s.evaluate('document.documentElement.scrollWidth <= innerWidth'),(slug,width)
                    if width in [1440,1024]:s.screenshot(path=str(OUT/f'ops-{slug}-{width}.png'),full_page=True)
                    checks.append((slug,width))
            a.goto(BASE+'/management/reports/')
            with a.expect_download() as download:
                a.get_by_role('link',name='Download CSV').click()
            assert 'Wait (minutes)' in Path(download.value.path()).read_text(encoding='utf-8')
            r.goto(BASE+f'/bookings/{booking.pk}/')
            expect(r.locator('.ticket-qr img')).to_be_visible()
            assert r.locator('.ticket-qr img').evaluate('(img)=>img.complete && img.naturalWidth>0')
            for width in [390,320]:
                r.set_viewport_size({'width':width,'height':844})
                for path,label in [('/resident/','Home'),('/bookings/','Bookings'),('/notifications/','Notifications'),('/profile/','Profile'),('/book/','Bookings'),(f'/bookings/{booking.pk}/','Bookings')]:
                    assert r.goto(BASE+path,wait_until='networkidle').status==200
                    nav=r.get_by_role('navigation',name='Resident navigation')
                    expect(nav).to_be_visible()
                    expect(nav.locator('a[aria-current=page]')).to_have_text(label)
                    r.evaluate('scrollTo(0,document.body.scrollHeight)')
                    assert nav.evaluate('(el)=>getComputedStyle(el).position==="fixed" && el.getBoundingClientRect().bottom<=innerHeight+1 && el.getBoundingClientRect().bottom>=innerHeight-1')
                    assert r.evaluate('document.documentElement.scrollWidth <= innerWidth'),(path,width)
                    if width==390:r.screenshot(path=str(OUT/('ops-resident-'+path.strip('/').replace('/','-')+'.png')))
                    checks.append((path,width))
            browser.close()
        assert not errors,errors
        (OUT/'operations-report.json').write_text(json.dumps({'checks':checks,'errors':errors},indent=2))
        print(f'PASS: QR arrival, staff calls/messages, resident replies, admin completion, priority walk-ins; {len(checks)} desktop/mobile layout checks.')
    finally:
        ScheduleException.objects.filter(created_by_id__in=ids).delete()
        WalkIn.objects.filter(registered_by_id__in=ids).delete()
        Booking.objects.filter(resident_id__in=ids).delete()
        AdminActivity.objects.filter(actor_id__in=ids).delete()
        User.objects.filter(pk__in=ids).delete()
        AppointmentSlot.objects.filter(pk=slot.pk).delete()
if __name__=='__main__':main()
