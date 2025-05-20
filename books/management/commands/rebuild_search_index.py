from django.core.management.base import BaseCommand
from django_elasticsearch_dsl.registries import registry
from books.search_indexes import BookDocument
from elasticsearch.exceptions import ConnectionError, TransportError
from books.utils.elasticsearch_client import ElasticsearchClient
import logging

# Configure logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Rebuild Elasticsearch index for books'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--models',
            nargs='+',
            type=str,
            help='List of model names to rebuild indexes for (e.g., Book)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Elasticsearch index rebuild...'))
        
        # Check Elasticsearch connection first
        self.stdout.write('Checking Elasticsearch connection...')
        if not ElasticsearchClient.check_connection(max_retries=3, retry_interval=2):
            self.stdout.write(self.style.ERROR('Cannot connect to Elasticsearch. Please ensure Elasticsearch is running.'))
            return
        
        models = options.get('models')
        if models:
            # Rebuild indexes for specified models
            for model_name in models:
                self.stdout.write(f'Rebuilding index for {model_name}...')
                try:
                    registry.rebuild(models=[model_name])
                    self.stdout.write(self.style.SUCCESS(f'Successfully rebuilt index for {model_name}'))
                except ConnectionError as e:
                    self.stdout.write(self.style.ERROR(f'Elasticsearch connection error rebuilding index for {model_name}: {e}'))
                    self.stdout.write('Please ensure Elasticsearch is running and accessible.')
                    return
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error rebuilding index for {model_name}: {e}'))
        else:
            # Rebuild all indexes
            try:
                # Rebuild the Book index specifically
                BookDocument().update()
                self.stdout.write(self.style.SUCCESS('Successfully rebuilt Book index'))
            except ConnectionError as e:
                self.stdout.write(self.style.ERROR(f'Elasticsearch connection error rebuilding Book index: {e}'))
                self.stdout.write('Please ensure Elasticsearch is running and accessible.')
                return
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error rebuilding Book index: {e}'))
                
        # Verify indices are populated
        try:
            if ElasticsearchClient.check_connection(max_retries=1):
                self.stdout.write('Verifying indices are populated...')
                # Simple check to see if we can search
                test_search, _ = ElasticsearchClient.search_books('test', page=1, page_size=1)
                if test_search is not None:
                    self.stdout.write(self.style.SUCCESS('Elasticsearch indices are searchable'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not verify search functionality: {e}'))
        
        self.stdout.write(self.style.SUCCESS('Elasticsearch index rebuild completed'))