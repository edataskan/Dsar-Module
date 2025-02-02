# load_cities.py
from django.core.management.base import BaseCommand
from core.models import City, Country

class Command(BaseCommand):
    help = 'Load cities into the database'

    def handle(self, *args, **kwargs):
        cities = [
            {'name': 'New York', 'country': 'United States'},
            {'name': 'Los Angeles', 'country': 'United States'},
            {'name': 'Toronto', 'country': 'Canada'},
            {'name': 'Vancouver', 'country': 'Canada'},
            # Daha fazla şehir ekleyebilirsiniz.
        ]
        
        for city in cities:
            country = Country.objects.get(name=city['country'])
            City.objects.get_or_create(name=city['name'], country=country)

        self.stdout.write(self.style.SUCCESS('Successfully loaded cities'))
