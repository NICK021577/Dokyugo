from django.conf import settings

def site(request):
    return {'barangay_name': settings.BARANGAY_NAME, 'hall_address': settings.HALL_ADDRESS,
            'office_hours': settings.OFFICE_HOURS, 'privacy_contact': settings.PRIVACY_CONTACT,
            'retention_period': settings.RETENTION_PERIOD}
