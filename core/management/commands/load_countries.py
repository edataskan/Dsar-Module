# load_countries.py
from django.core.management.base import BaseCommand
from core.models import Country

class Command(BaseCommand):
    help = 'Load countries into the database'

    def handle(self, *args, **kwargs):
        countries = [
            {'name': 'United States'},
            {'name': 'Canada'},
            # Daha fazla ülke ekleyebilirsiniz.
        ]
        
        for country in countries:
            Country.objects.get_or_create(name=country['name'])

        self.stdout.write(self.style.SUCCESS('Successfully loaded countries'))
