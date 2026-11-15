"""Account editing/access/deletion QA, using isolated temporary accounts only."""
import os
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import AdminActivity, AppointmentSlot, Booking, Document, ResidentProfile
from core import services
from playwright.sync_api import sync_playwright, expect

BASE=os.getenv('DOKYUGO_TEST_URL','http://127.0.0.1:8000')
OUT=ROOT/'artifacts'
OUT.mkdir(exist_ok=True)
POOL=ThreadPoolExecutor(max_workers=1)
def db(operation):
    return POOL.submit(operation).result()

def main():
    token=uuid.uuid4().hex[:10]
    password=uuid.uuid4().hex+'aA!'
    User=get_user_model()
    admin=User.objects.create_superuser(username=f'qa-account-admin-{token}@example.test',email=f'qa-account-admin-{token}@example.test',password=password,first_name='QA',last_name='Administrator')
    target=User.objects.create_user(username=f'qa-account-user-{token}@example.test',email=f'qa-account-user-{token}@example.test',password=password,first_name='QA',last_name='Resident')
    unused=User.objects.create_user(username=f'qa-account-unused-{token}@example.test',email=f'qa-account-unused-{token}@example.test',password=password,first_name='QA',last_name='Unused')
    ids=[admin.pk,target.pk,unused.pk]
    mobile='09'+str(int(uuid.uuid4().hex[:10],16))[-9:].zfill(9)
    ResidentProfile.objects.create(user=target,mobile=mobile)
    slot=AppointmentSlot.objects.create(starts_at=timezone.now()+timedelta(days=12,microseconds=713),capacity=1)
    doc=Document.objects.first()
    assert doc,'Seed the document catalogue first.'
    booking=services.book(target,[doc],slot,uuid.uuid4())
    new_email=f'qa-account-edited-{token}@example.test'
    new_password=uuid.uuid4().hex+'bB!'
    errors=[]
    checks=0
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
            page=browser.new_page(viewport={'width':1280,'height':960})
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(BASE+'/login/')
            page.locator('#id_username').fill(admin.username)
            page.locator('#id_password').fill(password)
            page.get_by_role('button',name='Log in',exact=True).click()
            page.wait_for_url('**/management/')
            edit_url=BASE+f'/management/accounts/{target.pk}/edit/'
            delete_url=BASE+f'/management/accounts/{target.pk}/delete/'
            for width in [1280,768,390,320]:
                page.set_viewport_size({'width':width,'height':960})
                for name,url in [('list',BASE+'/management/accounts/?q='+token),('edit',edit_url),('delete',delete_url)]:
                    response=page.goto(url,wait_until='networkidle')
                    assert response.status==200,(name,response.status)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(name,width)
                    if width in [1280,390]:
                        page.screenshot(path=str(OUT/f'account-{name}-{width}.png'),full_page=True)
                    checks+=1
            page.set_viewport_size({'width':1280,'height':960})
            page.goto(edit_url)
            page.get_by_label('First name',exact=True).fill('Updated')
            page.get_by_label('Email / login',exact=True).fill(new_email)
            page.get_by_label('Residential address',exact=True).fill('Updated barangay address')
            page.get_by_label('Role',exact=True).select_option('staff')
            page.get_by_label('New password',exact=True).fill(new_password)
            page.get_by_label('Confirm new password',exact=True).fill(new_password)
            page.get_by_role('button',name='Save account changes').click()
            page.wait_for_url(edit_url)
            db(target.refresh_from_db)
            assert target.first_name=='Updated' and target.is_staff and target.email==new_email
            other=browser.new_context().new_page()
            other.goto(BASE+'/login/')
            other.locator('#id_username').fill(new_email)
            other.locator('#id_password').fill(new_password)
            other.get_by_role('button',name='Log in',exact=True).click()
            other.wait_for_url('**/staff/')
            page.goto(BASE+'/management/accounts/?q='+new_email)
            row=page.get_by_role('row').filter(has=page.get_by_text(new_email,exact=True))
            row.get_by_label('Allow sign-in').uncheck()
            row.get_by_role('button',name='Save access').click()
            page.wait_for_url('**/management/accounts/')
            assert other.request.get(BASE+'/api/me/').status==401
            page.goto(edit_url)
            page.get_by_label('Role',exact=True).select_option('resident')
            page.get_by_label('Allow sign-in',exact=True).check()
            page.get_by_role('button',name='Save account changes').click()
            page.wait_for_url(edit_url)
            page.goto(delete_url)
            page.get_by_label('Type the account email or login to confirm').fill('wrong@example.test')
            page.get_by_label('I understand that sign-in').check()
            page.get_by_role('button',name='Confirm account deletion').click()
            expect(page.get_by_text('The confirmation does not match this account.',exact=True)).to_be_visible()
            page.get_by_label('Type the account email or login to confirm').fill(new_email)
            page.get_by_role('button',name='Confirm account deletion').click()
            page.wait_for_url('**/management/accounts/')
            db(target.refresh_from_db); db(booking.refresh_from_db); db(slot.refresh_from_db)
            assert not target.is_active and booking.status=='cancelled' and slot.reserved==0
            page.goto(BASE+'/management/accounts/?status=deleted&q='+new_email)
            page.get_by_role('button',name='Restore as inactive',exact=True).click()
            page.wait_for_url(edit_url)
            expect(page.get_by_label('Allow sign-in',exact=True)).not_to_be_checked()
            page.goto(BASE+f'/management/accounts/{unused.pk}/delete/')
            page.get_by_label('Deletion method',exact=True).select_option('permanent')
            page.get_by_label('Type the account email or login to confirm').fill(unused.email)
            page.get_by_label('I understand that sign-in').check()
            page.get_by_role('button',name='Confirm account deletion').click()
            page.wait_for_url('**/management/accounts/')
            assert not db(lambda:User.objects.filter(pk=unused.pk).exists())
            browser.close()
        assert not errors,errors
        print(f'PASS: {checks} responsive account-page checks; edit/password/login, access revocation, deletion confirmation, booking capacity release, restoration and permanent deletion.')
    finally:
        # Only the explicitly identified accounts and records created by this run.
        Booking.objects.filter(pk=booking.pk).delete()
        slot.delete()
        AdminActivity.objects.filter(actor_id=admin.pk).delete()
        User.objects.filter(pk__in=ids).delete()
        POOL.shutdown(wait=True)

if __name__=='__main__':
    main()
