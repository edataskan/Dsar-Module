import csv
from django.core.management.base import BaseCommand
from core.models import Country, City

class Command(BaseCommand):
    help = 'Load countries and cities into the database'

    def handle(self, *args, **kwargs):
        # Load countries
        with open('C:/Users/EXCALIBUR/Downloads/yeni/Django-Ecommerce-master/core/management/commands/cleaned_countries.csv', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                Country.objects.get_or_create(name=row['name'])

        # Load cities
        with open('C:/Users/EXCALIBUR/Downloads/yeni/Django-Ecommerce-master/core/management/commands/cleaned_cities.csv', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                country, created = Country.objects.get_or_create(name=row['country'])
                City.objects.get_or_create(name=row['name'], country=country)

        self.stdout.write(self.style.SUCCESS('Successfully loaded countries and cities'))
