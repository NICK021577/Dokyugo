# Admin and calendar update validation

Verified locally on November 14, 2026, Asia/Manila.

- 35 Django tests passed, including all existing tests and new administration/calendar cases.
- 29 browser viewport checks passed across the admin dashboard, schedule, documents, accounts, activity and resident calendar/review screens.
- Browser role checks passed: admin, staff and resident logins open their respective workspaces; staff and residents receive 403 for the administrator workspace.
- The full browser flow passed using real calendar buttons: registration, document selection, date/time choice, review/confirmation, rescheduling, cancellation, staff processing and the matching resident ticket status.
- 12 additional resident viewport checks passed at 390px and 320px.
- Calendar browser checks also used an America/Los_Angeles browser timezone; displayed appointments remain in Philippine time.
- Django system checks, migration consistency and JavaScript syntax checks passed.
- Temporary QA accounts and bookings created by browser tests were removed. The three explicitly requested demo accounts remain and expire November 21, 2026. Demo authentication is disabled in production mode.

Screenshots and detailed browser reports are in the ignored artifacts directory. Tests used a separate test database; the user's existing resident account was preserved. No external SMS service or production deployment was added.
