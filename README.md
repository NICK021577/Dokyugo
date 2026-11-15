# DokyuGo

Django website for barangay document requirements, resident appointments and the staff queue. Public pages follow the inspected DokyuGo Figma file and the updated screenshot. Templates, CSS, fonts and original SVG assets are local; no frontend framework or build step is required.

## Run locally on Windows

The project virtual environment and initial SQLite database are already prepared in this workspace.

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Open http://127.0.0.1:8000/. Register a resident account using **Create an account**. Create an administrator separately:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

The username for an administrator can be an email address. All roles sign in through `/login/`: administrators are taken to `/management/`, staff to `/staff/`, and residents to `/resident/`. The branded admin dashboard manages schedules, documents, requirements, account access and an activity log. Django's advanced administration remains at `/admin/`.

### Temporary local testing accounts

These accounts were created at the user's request and expire after seven days. They are rejected automatically when `DJANGO_DEBUG=0`. They are not installed automatically by migrations or normal setup.

| Role | Email / username | Temporary password | Landing page |
| --- | --- | --- | --- |
| Administrator | `admin@dokyugo.test` | `AdminDemo!2026` | `/management/` |
| Staff | `staff@dokyugo.test` | `StaffDemo!2026` | `/staff/` |
| Resident / user | `user@dokyugo.test` | `UserDemo!2026` | `/resident/` |

```powershell
# Create missing demo accounts; preserves existing passwords and expiry dates:
.\.venv\Scripts\python.exe manage.py create_demo_accounts
# Explicitly reset demo passwords and renew the seven-day test period:
.\.venv\Scripts\python.exe manage.py create_demo_accounts --reset-passwords
# Deactivate the marked test accounts without deleting their booking history:
.\.venv\Scripts\python.exe manage.py create_demo_accounts --disable
```

An existing unmarked account with a matching username is never overwritten. Create a separate permanent administrator for production.

### Calendar booking and administration

Residents now select a month, an available date, and a morning/afternoon time card showing remaining places. Full, closed and past times are disabled. The picker reads current database availability; the backend still rechecks capacity at confirmation. Rescheduling uses the same picker, excludes the current time, and enforces the 24-hour cutoff. Calendar labels and appointment times use Asia/Manila even when a browser uses another timezone. A standard appointment list remains available without JavaScript or if the availability request fails.

The booking page includes document search, a live appointment summary and a review step before confirmation. The profile form now saves a middle name and residential address, following the resident workflow in the supplied Word document.

At `/management/`, administrators can:

- View daily totals, waiting/completed appointments, a seven-day booking chart and recent changes.
- Publish appointment slots for one day or a date range, with time intervals, capacity and optional weekday filtering. Existing slots are preserved.
- Open/close individual times or change capacity. Closing a time preserves existing appointments; capacity cannot be reduced below reservations.
- Add/edit document descriptions, requirements, fees, processing time and booking availability. Public pages and the mobile API use these same records.
- Edit names, login email, mobile number, residential address, resident/staff roles and optional passwords. Duplicate emails/mobiles and invalid passwords are rejected. Access changes revoke existing sessions. Administrator personal details and passwords can be edited, while their role and sign-in state stay protected on these pages.
- Delete accounts through a typed email/login confirmation. Deleted accounts are hidden from the current list and cannot sign in; pending bookings are cancelled and reserved places released. Booking and activity history is retained. Accounts currently being served must finish their service first.
- Find deleted accounts with the status filter and restore them as inactive. Review the details and explicitly enable sign-in; cancelled bookings are not reinstated. Permanent deletion is available only for accounts without any booking or authored activity history. Administrator accounts cannot be deleted through these controls.
- Search accounts by name, email, login or mobile, filter by role/status, and browse paginated results.
- Read administrative and booking activity. Staff can call/recall residents and send appointment messages; administrators record arrivals, register walk-ins, start/complete service and manage settings.

### Desktop operations and resident phone navigation

Staff `/staff/` and admin `/management/` use desktop workspaces with persistent sidebars. Staff see both windows, waiting counts, current residents and a two-pane resident inbox. Queue counts refresh every 15 seconds; a change notice offers an explicit refresh without clearing a message draft. The staff inbox sends database-backed in-app messages and residents reply from their ticket. “Open dialer” uses `tel:` and needs a configured calling application on the PC; browser VoIP and SMS delivery are not integrated.

Residents on phones have a fixed Home / Bookings / Notifications / Profile navigation bar, including a highlighted current location and safe-area spacing. Ticket pages include a signed QR image and a link to their private appointment conversation.

The selected updates **2, 3, 5 and 6** are implemented:

- **Walk-ins and priority:** `/management/walk-ins/` issues daily `W-001` tickets for Window 2. Senior/PWD residents are called first, then arrival order within each priority group. Window 1 calls checked-in appointments by scheduled time. A window must finish its current service before staff call the next resident.
- **QR arrival:** `/management/check-in/` previews the signed ticket before an administrator explicitly records arrival. Use a USB QR reader, paste the QR link, or use a camera where the browser supports `BarcodeDetector` and camera access. The QR alone cannot record an arrival. Check-in opens 30 minutes before the scheduled time, on its scheduled day, and closes after a 15-minute grace period. Repeated check-in is safe. Signed QR links expire after 120 days; reopening the resident ticket generates a fresh link.
- **Calendar planning:** `/management/opening-hours/` saves recurring weekdays, hours, breaks, capacity and service scope. `/management/closures/` previews holidays/breaks/service exceptions and affected confirmed appointments. Publishing a closure blocks new bookings and sends affected residents an in-app notice; existing bookings remain for admin follow-up. Appointment slot settings support service scopes, duration and capacity without overwriting reserved places. The resident calendar and booking backend both enforce service availability.
- **Reports:** `/management/reports/` filters by date, window and document, with CSV downloads, document demand, missed appointments, waiting and processing times. Wait is actual check-in to first call; processing is actual start to completion. Missing historical timestamps remain unrecorded and do not enter timing averages.

Administrators update processing/completion at `/management/queue/`. These actions are rejected for staff even if submitted directly. All operations use the same Django database as resident bookings.

For a fresh checkout:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
# Optional, local demonstrations only:
.\.venv\Scripts\python.exe manage.py seed_demo --slots
.\.venv\Scripts\python.exe manage.py runserver
```

`seed_demo` loads the 17 document names/descriptions from the design without overwriting staff edits. `--slots` adds sample weekday availability for the next 14 days. The sample hours and capacity are demonstration data, not confirmed barangay operating hours. Remove or replace these slots before using the system for real appointments. Unknown requirements, fees and processing times retain the design's explicit placeholders.

## Pages and shared backend

- Public: `/`, `/documents/`, `/documents/<slug>/`, `/how-it-works/`, `/privacy/`.
- Accounts: `/signup/`, `/login/`, `/password-reset/` and Django's signed, expiring reset links.
- Responsive resident portal: `/resident/`, `/book/`, `/bookings/`, individual tickets, rescheduling, cancellation, notifications and profile/password editing.
- Staff: `/staff/` for a date-filtered queue. Administrator: `/management/`, with `/admin/` retained for advanced configuration.

The resident portal, staff website and JSON API all use the same Django models and SQLite database. No separate mobile database is created. There was no existing native mobile client in this workspace; this delivery supplies the responsive resident portal and integration endpoints, rather than claiming a native Android/iOS build. The Word document's embedded designs were inspected as context; the updated website reference governs public-page styling.

Queue numbers are unique per local appointment date. Reservations use a conditional database update inside a transaction so a full slot cannot be overbooked. A submission UUID prevents duplicate bookings. Cancellation/rescheduling release capacity atomically and require at least 24 hours' notice. Staff status changes are audited and create resident notifications. Ticket status polls the same booking record every 15 seconds while visible. Checklists store only preparation checkmarks in the browser; no resident identity or booking data is stored in localStorage.

## JSON API for a mobile client

Use a cookie-preserving HTTP client against the same backend origin. First `GET /api/csrf/`, retain its cookies, and send the returned token as `X-CSRFToken` on every POST. Login/signup rotate the CSRF token and return the new value. Do not disable CSRF or add wildcard CORS to integrate a client.

| Endpoint | Method | Result |
| --- | --- | --- |
| `/api/csrf/` | GET | CSRF token and cookie |
| `/api/signup/` | POST | Register with the same fields as the website; establish session |
| `/api/login/` | POST | `username` (email/mobile), `password`; establish session |
| `/api/logout/` | POST | End session |
| `/api/me/` | GET | Signed-in account |
| `/api/documents/` | GET | Catalogue and current requirements |
| `/api/slots/?date=YYYY-MM-DD` | GET | Future open slots and remaining capacity |
| `/api/availability/?month=YYYY-MM` | GET | Signed-in monthly calendar, available dates, remaining places and disabled time states |
| `/api/bookings/` | GET, POST | Resident bookings / create booking |
| `/api/bookings/<uuid>/` | GET | Owner's live ticket status |
| `/api/bookings/<uuid>/cancel/` | POST | Cancel under the same website rules |
| `/api/bookings/<uuid>/reschedule/` | POST | Reschedule with `slot` ID |
| `/api/notifications/` | GET, POST | Notifications / mark all as read |

Create-booking JSON example (replace the document/slot IDs with catalogue responses and generate a fresh UUID per intended booking; reuse it only to retry that submission):

```json
{"documents": [1], "slot": 1, "submission_key": "04fd9b78-a79e-493c-adbf-ae733f48ae49", "prepared": true}
```

## Email and scheduled work

Local email is saved in the ignored `emails/` directory. Password reset accepts email or mobile and sends the reset link to the matching account's email address. Booking confirmation and rescheduling emails are written after the database commit. Emails are not delivered externally until SMTP is configured. SMS delivery is not integrated; the design's SMS reminder copy requires a provider before a live launch.

Configure actual delivery through environment variables `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` and `DEFAULT_FROM_EMAIL`. Environment variables are read directly; no `.env` loader is required or implied.

Schedule one instance of each command using Windows Task Scheduler or your deployment scheduler:

```powershell
# Daily, for the next day's appointments (Asia/Manila):
.\.venv\Scripts\python.exe manage.py send_reminders
# Every minute, to apply the stated 15-minute grace period:
.\.venv\Scripts\python.exe manage.py expire_bookings
# Daily, to publish the next 30 days from active saved opening-hour rules:
.\.venv\Scripts\python.exe manage.py publish_schedules
```

Reminders record successful delivery to avoid sequential duplicate sends. Do not run overlapping copies of the reminder task. The development server itself does not schedule these commands. Checked-in residents are excluded from automatic missed-booking expiry. Recurring publishing respects each rule's date range, breaks and applicable closures, and preserves existing slots.

## Verification

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

Optional browser QA requires `requirements-dev.txt` and installed Google Chrome at the path in the scripts. With the local server running:

```powershell
.\.venv\Scripts\python.exe scripts/browser_check.py
.\.venv\Scripts\python.exe scripts/browser_flow.py
.\.venv\Scripts\python.exe scripts/browser_updates.py
.\.venv\Scripts\python.exe scripts/browser_accounts.py
.\.venv\Scripts\python.exe scripts/browser_operations.py
```

The first script checks the eight public pages at 1280, 768, 390 and 320 pixels, image loading, horizontal overflow, mobile menu, FAQ and saved checklists. The second uses actual forms and calendar buttons to register a temporary QA resident, review/book/reschedule/cancel, then update another booking through administrator service controls and verify the resident sees the change. It removes its identified QA accounts/bookings afterward. The third checks admin pages, role isolation and responsive calendar/review layouts using the seeded demo accounts. Set `DOKYUGO_TEST_URL` to test the latter two scripts on a different local port. Screenshots/reports are saved under the ignored `artifacts/` directory.

`browser_accounts.py` creates isolated temporary accounts and exercises the account editor, password/login changes, session revocation, deletion confirmation, booking cancellation/capacity release, restoration and permanent deletion. It checks the list/editor/deletion pages at four widths and removes only its own QA records afterward. It also supports `DOKYUGO_TEST_URL`.

`browser_operations.py` exercises QR arrival, staff calls/messages, resident replies, administrator completion, priority walk-ins, reports, desktop pages at 1440/1280/1024 and fixed resident navigation at 390/320. It refuses to run while unrelated residents are being served or waiting at the desk, and removes only its own QA records. Use a local test database. Physical camera/hardware scanner access is not simulated by this headless check.

## Deployment configuration

This is a local Django project; it has not been deployed. Use a Python WSGI/ASGI host and one shared database for website and mobile requests. Sites' static/Worker hosting cannot run this Django application as-is.

Set `DJANGO_DEBUG=0`, a random `DJANGO_SECRET_KEY`, and `DJANGO_ALLOWED_HOSTS` for your domain. Production mode enables HTTPS-only cookies and HTTPS redirection; terminate HTTPS correctly at your host. Run `collectstatic` and serve `staticfiles/`. The generated development secret is in the ignored `.local-secret` file. Use a shared cache for throttling in a deployment with multiple processes and a database suitable for the expected concurrent workload. Preserve/migrate the same database for both resident and staff access.

Set `BARANGAY_NAME`, `HALL_ADDRESS`, `OFFICE_HOURS`, `PRIVACY_CONTACT` and `RETENTION_PERIOD` to confirmed values. The privacy notice reproduces design-provided draft text; confirm its retention period, contact, update date and actual notification providers before publication. No fees or policy details were invented.

Design inspection and screen inventory: [reference/inspection.md](reference/inspection.md).

Ideas for the next iteration: [FUTURE_UPDATES.md](FUTURE_UPDATES.md).
