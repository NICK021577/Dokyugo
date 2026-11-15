import json
from datetime import datetime, time, timedelta
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from core.models import AppointmentSlot, Document, Requirement

class Command(BaseCommand):
    help = 'Load the Figma document catalogue and optional local demonstration appointments. Does not overwrite staff edits.'
    def add_arguments(self, parser):
        parser.add_argument('--slots', action='store_true', help='Create 14 days of DEMO weekday slots (8am–4pm). Not official office hours.')
    def handle(self, *args, **options):
        rows = json.loads((Path(__file__).resolve().parents[2] / 'data/documents.json').read_text(encoding='utf-8'))
        for row in rows:
            doc, created = Document.objects.get_or_create(slug=slugify(row['name']), defaults=row)
            if created:
                texts = ['Valid ID showing your address', 'Proof of residency', '[REQUIREMENT TO CONFIRM]', '[REQUIREMENT TO CONFIRM]'] if row['position'] == 0 else ['[REQUIREMENT TO CONFIRM]']
                Requirement.objects.bulk_create([Requirement(document=doc, text=text, position=i, confirmed=row['position'] == 0 and i < 2) for i, text in enumerate(texts)])
        self.stdout.write(self.style.SUCCESS(f'Catalogue ready: {Document.objects.count()} documents. Existing edits preserved.'))
        if options['slots']:
            for offset in range(1, 15):
                day = timezone.localdate() + timedelta(days=offset)
                if day.weekday() >= 5:
                    continue
                for hour in range(8, 16):
                    if hour == 12:
                        continue
                    for minute in (0, 30):
                        AppointmentSlot.objects.get_or_create(starts_at=timezone.make_aware(datetime.combine(day, time(hour, minute))))
            self.stdout.write(self.style.WARNING('DEMO slots created. Replace this schedule with confirmed office availability before production.'))
