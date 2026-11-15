"""Local visual QA. Start manage.py runserver on port 8000 first."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts'
OUT.mkdir(exist_ok=True)
PAGES = {'home': '/', 'documents': '/documents/', 'requirements': '/documents/barangay-clearance/',
         'how': '/how-it-works/', 'privacy': '/privacy/', 'signup': '/signup/', 'login': '/login/', 'reset': '/password-reset/'}

def main():
    errors, checks = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe', headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 900}, device_scale_factor=1)
        page.on('pageerror', lambda error: errors.append(str(error)))
        for width in [1280, 768, 390, 320]:
            page.set_viewport_size({'width': width, 'height': 900})
            for name, path in PAGES.items():
                response = page.goto('http://127.0.0.1:8000' + path, wait_until='networkidle')
                page.evaluate('document.fonts.ready')
                page.evaluate('''async () => {
                    const imgs = [...document.images];
                    imgs.forEach(i => i.loading = 'eager');
                    await Promise.all(imgs.map(i => i.decode().catch(() => {})));
                }''')
                assert response.status == 200, (name, response.status)
                details = page.evaluate('''() => ({
                    overflow: document.documentElement.scrollWidth > innerWidth,
                    width: document.documentElement.scrollWidth,
                    brokenImages: [...document.images].filter(i => !i.complete || !i.naturalWidth).map(i => i.src),
                    images: [...document.images].map(i => ({src: i.getAttribute('src'), width:i.getBoundingClientRect().width, height:i.getBoundingClientRect().height, visible:!!i.getClientRects().length})),
                    h1: document.querySelector('h1')?.textContent,
                    height: document.documentElement.scrollHeight
                })''')
                checks.append({'page': name, 'viewport': width, **details})
                assert not details['brokenImages'], (name, details['brokenImages'])
                if details['overflow']:
                    errors.append(f'{name} overflows at {width}px: {details["width"]}px')
                if width in [1280, 390]:
                    page.screenshot(path=str(OUT / f'{name}-{width}.png'), full_page=True)
        page.set_viewport_size({'width': 390, 'height': 900})
        page.goto('http://127.0.0.1:8000/')
        page.get_by_role('button', name='Menu').click()
        assert page.get_by_role('button', name='Menu').get_attribute('aria-expanded') == 'true'
        page.keyboard.press('Escape')
        assert page.get_by_role('button', name='Menu').get_attribute('aria-expanded') == 'false'
        page.goto('http://127.0.0.1:8000/how-it-works/')
        page.get_by_text('Do I need a smartphone?', exact=True).click()
        assert page.locator('details').nth(2).get_attribute('open') is not None
        page.goto('http://127.0.0.1:8000/documents/barangay-clearance/')
        first = page.locator('[data-checklist] input').first
        first.check()
        page.reload()
        assert page.locator('[data-checklist] input').first.is_checked()
        browser.close()
    (OUT / 'browser-report.json').write_text(json.dumps({'checks': checks, 'errors': errors}, indent=2), encoding='utf-8')
    assert not errors, errors
    print(f'PASS: {len(checks)} page/viewport checks; assets, overflow, menu, FAQ and saved checklists verified.')

if __name__ == '__main__':
    main()
