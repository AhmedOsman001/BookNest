# recommendations/management/commands/export_recommendation_data.py
from django.core.management.base import BaseCommand
from recommendation.tocsv import export_data_to_csv

class Command(BaseCommand):
    help = 'Export book and ratings data to CSV files for recommendation system'

    def handle(self, *args, **options):
        self.stdout.write('Exporting recommendation data to CSV...')
        export_data_to_csv()
        self.stdout.write(self.style.SUCCESS('Successfully exported recommendation data!'))