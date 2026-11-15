"""Exercise real forms, CSRF/session cookies, booking and staff updates in Chrome.
Creates temporary local QA accounts and removes their records on completion.
"""
import os
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from django.db.models import F
from django.utils import timezone
from datetime import timedelta
from core.models import AppointmentSlot, Booking, QueueCounter
from playwright.sync_api import sync_playwright, expect

BASE_URL = os.getenv('DOKYUGO_TEST_URL', 'http://127.0.0.1:8000')
OUT = ROOT / 'artifacts'
OUT.mkdir(exist_ok=True)
DB_POOL = ThreadPoolExecutor(max_workers=1)

def db_call(operation):
    # Playwright's sync bridge runs an event loop; keep ORM work on its own thread.
    return DB_POOL.submit(operation).result()

def choose_slot(page, slot):
    key = timezone.localtime(slot.starts_at).date().isoformat()
    page.locator('[data-calendar-grid] button:not([disabled])').first.wait_for()
    for _ in range(12):
        if page.locator(f'[data-date="{key}"]').count():
            break
        page.locator('[data-month-next]').click()
        page.wait_for_function("!document.querySelector('[data-appointment-picker]').hasAttribute('aria-busy')")
    page.locator(f'[data-date="{key}"]').click()
    page.locator(f'[data-slot="{slot.pk}"]').click()
    expect(page.locator('#id_slot')).to_have_value(str(slot.pk))

def main():
    suffix = uuid.uuid4().hex[:10]
    email = f'qa-{suffix}@example.test'
    staff_email = f'qa-staff-{suffix}@example.test'
    password = uuid.uuid4().hex + '!aA'
    mobile = '09' + str(int(uuid.uuid4().hex[:10], 16))[-9:].zfill(9)
    staff = get_user_model().objects.create_user(username=staff_email, email=staff_email, password=password, first_name='QA', last_name='Administrator', is_staff=True, is_superuser=True)
    created_bookings = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe', headless=True)
            context = browser.new_context(viewport={'width': 390, 'height': 900})
            page = context.new_page()
            page.goto(BASE_URL + '/signup/')
            page.get_by_label('Last name', exact=True).fill('Resident')
            page.get_by_label('First name', exact=True).fill('QA')
            page.get_by_label('I have no middle name', exact=True).check()
            assert page.get_by_label('Middle name', exact=True).is_disabled()
            page.get_by_label('Mobile number', exact=True).fill(mobile)
            page.get_by_label('Email', exact=True).fill(email)
            page.get_by_label('Password', exact=True).fill(password)
            page.locator('#id_privacy').check()
            page.get_by_role('button', name='Create account', exact=True).click()
            page.wait_for_url('**/resident/')
            page.screenshot(path=str(OUT / 'resident-home-390.png'), full_page=True)
            page.goto(BASE_URL + '/book/')
            page.locator('input[name=documents]').first.check()
            slot = db_call(lambda: AppointmentSlot.objects.filter(starts_at__gte=timezone.now()+timedelta(hours=48), reserved__lt=F('capacity'), is_open=True).first())
            assert slot, 'Run seed_demo --slots before this test.'
            choose_slot(page, slot)
            page.locator('#id_prepared').check()
            page.get_by_role('button', name='Review appointment').click()
            page.get_by_role('button', name='Confirm booking').click()
            page.wait_for_url('**/bookings/*/')
            booking = db_call(lambda: Booking.objects.get(resident__username=email))
            created_bookings.append(booking.pk)
            assert page.get_by_text(booking.ticket, exact=True).count() >= 1
            ticket_url = page.url
            page.screenshot(path=str(OUT / 'resident-ticket-390.png'), full_page=True)
            page.get_by_role('link', name='Reschedule', exact=True).click()
            new_slot = db_call(lambda: AppointmentSlot.objects.filter(starts_at__gte=timezone.now()+timedelta(hours=48), reserved__lt=F('capacity'), is_open=True).exclude(pk=slot.pk).first())
            choose_slot(page, new_slot)
            page.get_by_role('button', name='Confirm new time').click()
            page.wait_for_url(ticket_url)
            db_call(booking.refresh_from_db)
            assert booking.slot_id == new_slot.pk
            page.get_by_role('link', name='Cancel booking', exact=True).click()
            page.get_by_role('button', name='Yes, cancel booking', exact=True).click()
            page.wait_for_url(ticket_url)
            db_call(booking.refresh_from_db)
            assert booking.status == 'cancelled'

            # Book again, then progress the same record through administrator service controls.
            page.goto(BASE_URL + '/book/')
            page.locator('input[name=documents]').first.check()
            choose_slot(page, slot)
            page.locator('#id_prepared').check()
            page.get_by_role('button', name='Review appointment').click()
            page.get_by_role('button', name='Confirm booking').click()
            page.wait_for_url('**/bookings/*/')
            booking = db_call(lambda: Booking.objects.filter(resident__username=email).exclude(status='cancelled').get())
            created_bookings.append(booking.pk)
            ticket_url = page.url
            staff_context = browser.new_context(viewport={'width': 1280, 'height': 900})
            staff_page = staff_context.new_page()
            staff_page.goto(BASE_URL + '/login/')
            staff_page.get_by_label('Mobile number or email', exact=True).fill(staff_email)
            staff_page.get_by_label('Password', exact=True).fill(password)
            staff_page.get_by_role('button', name='Log in', exact=True).click()
            staff_page.wait_for_url('**/management/')
            day = timezone.localtime(slot.starts_at).date().isoformat()
            for action, expected in [('Call number', 'called'), ('Start processing', 'processing'), ('Complete', 'completed')]:
                staff_page.goto(BASE_URL + f'/management/queue/?date={day}')
                row = staff_page.get_by_role('row').filter(has_text=booking.ticket)
                row.locator('select[name=status]').select_option(expected)
                row.get_by_role('button', name='Save', exact=True).click()
                staff_page.wait_for_url('**/management/queue/?date=*')
                db_call(booking.refresh_from_db)
                assert booking.status == expected, (action, booking.status)
            page.goto(ticket_url)
            assert page.locator('[data-ticket-status]').inner_text() == 'Completed'
            staff_page.goto(BASE_URL + f'/management/queue/?date={day}')
            staff_page.screenshot(path=str(OUT / 'staff-queue-1280.png'), full_page=True)
            for width in [390, 320]:
                page.set_viewport_size({'width': width, 'height': 900})
                for path in ['/resident/', '/bookings/', '/book/', '/profile/', '/notifications/', '/profile/password/']:
                    response = page.goto(BASE_URL+path)
                    assert response.status == 200
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, path)
            browser.close()
        print('PASS: mobile signup, booking, reschedule, cancel, admin service transitions and shared resident status; 12 resident viewport checks.')
    finally:
        # Delete only this run's identified QA rows and restore their slot counts.
        for booking in Booking.objects.filter(resident__username=email):
            if booking.status != 'cancelled':
                AppointmentSlot.objects.filter(pk=booking.slot_id, reserved__gt=0).update(reserved=F('reserved')-1)
            booking.delete()
        get_user_model().objects.filter(username__in=[email, staff_email]).delete()

if __name__ == '__main__':
    main()
