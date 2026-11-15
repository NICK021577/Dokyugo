"""Check calendar and administrative views using the explicitly seeded demo accounts."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts'
OUT.mkdir(exist_ok=True)
BASE=os.getenv('DOKYUGO_TEST_URL','http://127.0.0.1:8000')

def signin(page,email,password):
    page.goto(BASE+'/login/')
    page.get_by_label('Mobile number or email',exact=True).fill(email)
    page.get_by_label('Password',exact=True).fill(password)
    page.get_by_role('button',name='Log in',exact=True).click()
    page.wait_for_url(lambda url: '/login/' not in url)

def main():
    report=[]
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
        admin_context=browser.new_context(viewport={'width':1440,'height':1000})
        page=admin_context.new_page()
        page.on('pageerror',lambda error:errors.append(str(error)))
        signin(page,'admin@dokyugo.test','AdminDemo!2026')
        assert page.url.endswith('/management/')
        for width in [1440,1280,768,390,320]:
            page.set_viewport_size({'width':width,'height':1000})
            for slug,path in [('admin','/management/'),('schedule','/management/schedule/'),('documents-admin','/management/documents/'),('accounts','/management/accounts/'),('activity','/management/activity/')]:
                response=page.goto(BASE+path,wait_until='networkidle')
                page.evaluate('document.fonts.ready')
                assert response.status==200,(path,response.status)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(path,width)
                report.append({'page':slug,'width':width,'status':response.status})
                if width in [1440,390]:
                    page.screenshot(path=str(OUT/f'update-{slug}-{width}.png'),full_page=True)
        resident_context=browser.new_context(viewport={'width':1280,'height':1000},timezone_id='America/Los_Angeles')
        resident=resident_context.new_page()
        resident.on('pageerror',lambda error:errors.append(str(error)))
        signin(resident,'user@dokyugo.test','UserDemo!2026')
        assert resident.url.endswith('/resident/')
        for width in [1280,768,390,320]:
            resident.set_viewport_size({'width':width,'height':1000})
            resident.goto(BASE+'/book/',wait_until='networkidle')
            resident.locator('[data-calendar-grid] button:not([disabled])').first.wait_for()
            resident.locator('input[name=documents]').first.check()
            resident.locator('[data-calendar-grid] button:not([disabled])').first.click()
            resident.locator('[data-slot]:not([disabled])').first.click()
            expect(resident.locator('#id_slot')).not_to_have_value('')
            assert resident.evaluate('document.documentElement.scrollWidth <= innerWidth'),('calendar',width)
            resident.locator('#id_prepared').check()
            resident.get_by_role('button',name='Review appointment').click()
            expect(resident.locator('[data-review-panel]')).to_be_visible()
            expect(resident.get_by_role('button',name='Confirm booking')).to_be_visible()
            resident.screenshot(path=str(OUT/f'update-calendar-{width}.png'),full_page=True)
            report.append({'page':'calendar-review','width':width,'status':200})
        assert resident.goto(BASE+'/management/').status==403
        staff_context=browser.new_context()
        staff=staff_context.new_page()
        signin(staff,'staff@dokyugo.test','StaffDemo!2026')
        assert staff.url.endswith('/staff/')
        assert staff.goto(BASE+'/management/').status==403
        browser.close()
    (OUT/'updates-report.json').write_text(json.dumps({'checks':report,'errors':errors},indent=2))
    assert not errors,errors
    print(f'PASS: {len(report)} admin/calendar viewport checks, review step, role redirects and admin access isolation.')

if __name__=='__main__':
    main()
