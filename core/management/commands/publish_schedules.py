from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import OpeningHours
from core.scheduling import publish,rule_data

class Command(BaseCommand):
    help='Publish upcoming appointments from active recurring opening hours, preserving existing slots and closures.'
    def handle(self,*args,**options):
        total=0
        for rule in OpeningHours.objects.filter(active=True,end_date__gte=timezone.localdate()).prefetch_related('documents'):
            result=publish(rule_data(rule),start=timezone.localdate(),end=timezone.localdate()+timedelta(days=30))
            total+=result['created']
        self.stdout.write(self.style.SUCCESS(f'Published {total} new recurring appointment slots.'))
