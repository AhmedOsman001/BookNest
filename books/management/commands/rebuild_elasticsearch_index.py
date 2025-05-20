from django.core.management.base import BaseCommand
from django_elasticsearch_dsl.registries import registry
from books.models import Book
from django.utils import timezone
from elasticsearch.exceptions import ConnectionError, TransportError
from books.utils.elasticsearch_client import ElasticsearchClient
import time
import logging

# Configure logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Rebuilds the Elasticsearch index for all books'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of books to index in each batch'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        start_time = time.time()
        self.stdout.write(self.style.SUCCESS(f'Starting Elasticsearch index rebuild at {timezone.now()}'))
        
        # Check Elasticsearch connection first
        self.stdout.write('Checking Elasticsearch connection...')
        if not ElasticsearchClient.check_connection(max_retries=3, retry_interval=2):
            self.stdout.write(self.style.ERROR('Cannot connect to Elasticsearch. Please ensure Elasticsearch is running.'))
            return
        
        # Delete existing index
        try:
            self.stdout.write('Deleting existing index...')
            registry.delete_all()
            self.stdout.write(self.style.SUCCESS('Successfully deleted existing indices'))
        except (ConnectionError, TransportError) as e:
            self.stdout.write(self.style.ERROR(f'Elasticsearch connection error when deleting indices: {str(e)}'))
            self.stdout.write('Please ensure Elasticsearch is running and accessible.')
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error deleting indices: {str(e)}'))
            return
        
        # Get total count of books
        total_books = Book.objects.count()
        if total_books == 0:
            self.stdout.write(self.style.WARNING('No books found in the database to index'))
            return
            
        self.stdout.write(f'Found {total_books} books to index')
        
        # Process in batches
        processed = 0
        errors = 0
        for i in range(0, total_books, batch_size):
            batch = Book.objects.all()[i:i+batch_size]
            self.stdout.write(f'Indexing batch {i//batch_size + 1} ({len(batch)} books)...')
            
            # Index the batch
            batch_errors = 0
            for book in batch:
                try:
                    registry.update(book)
                    processed += 1
                except (ConnectionError, TransportError) as e:
                    errors += 1
                    batch_errors += 1
                    self.stdout.write(
                        self.style.ERROR(f'Elasticsearch connection error indexing book {book.isbn13}: {str(e)}')
                    )
                    # If we're getting connection errors, check if Elasticsearch is still available
                    if batch_errors > 5:  # If we have multiple errors in a batch, check connection
                        if not ElasticsearchClient.check_connection(max_retries=1):
                            self.stdout.write(self.style.ERROR('Lost connection to Elasticsearch. Aborting indexing.'))
                            break
                except Exception as e:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(f'Error indexing book {book.isbn13}: {str(e)}')
                    )
            
            # Print progress
            if processed > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'Progress: {processed}/{total_books} books indexed ({processed/total_books*100:.1f}%)')
                )
            
            # If we lost connection, break out of the loop
            if batch_errors > 5 and not ElasticsearchClient.check_connection(max_retries=1):
                break
        
        # Print summary
        end_time = time.time()
        duration = end_time - start_time
        
        if processed == 0:
            self.stdout.write(
                self.style.ERROR(
                    f'Elasticsearch index rebuild failed. No books were indexed.\n'
                    f'Please check Elasticsearch connection and logs.'
                )
            )
        else:
            success_rate = (processed / total_books) * 100
            status_style = self.style.SUCCESS if success_rate > 90 else self.style.WARNING
            
            self.stdout.write(
                status_style(
                    f'Elasticsearch index rebuild completed at {timezone.now()}\n'
                    f'Total time: {duration:.2f} seconds\n'
                    f'Books indexed: {processed}/{total_books} ({success_rate:.1f}%)\n'
                    f'Errors encountered: {errors}'
                )
            )