from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError, TransportError
from django_elasticsearch_dsl.registries import registry
import time
import requests
import socket
import logging

# Configure logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Initialize Elasticsearch and create indices if they do not exist'

    def add_arguments(self, parser):
        parser.add_argument(
            '--wait',
            action='store_true',
            help='Wait for Elasticsearch to become available'
        )
        parser.add_argument(
            '--max-retries',
            type=int,
            default=30,
            help='Maximum number of connection retries'
        )
        parser.add_argument(
            '--retry-interval',
            type=int,
            default=2,
            help='Seconds to wait between retries'
        )

    def check_dns_resolution(self, host):
        """Check if the hostname can be resolved"""
        try:
            # Extract hostname from host string (e.g., 'elasticsearch:9200' -> 'elasticsearch')
            hostname = host.split(':')[0]
            socket.gethostbyname(hostname)
            return True
        except socket.gaierror:
            return False
    
    def handle(self, *args, **options):
        wait = options['wait']
        max_retries = options['max_retries']
        retry_interval = options['retry_interval']
        
        # Get Elasticsearch connection settings
        es_hosts = getattr(settings, 'ELASTICSEARCH_DSL', {}).get('default', {}).get('hosts', ['localhost:9200'])
        
        self.stdout.write(f"Connecting to Elasticsearch at {es_hosts}...")
        
        # Try to connect to Elasticsearch
        connected = False
        retries = 0
        
        while not connected and (not wait or retries < max_retries):
            # First check DNS resolution
            if not self.check_dns_resolution(es_hosts[0]):
                self.stdout.write(self.style.WARNING(f"DNS resolution failed for {es_hosts[0]}"))
                if wait:
                    self.stdout.write(f"Waiting for DNS to be available, retrying in {retry_interval} seconds... ({retries+1}/{max_retries})")
                    time.sleep(retry_interval)
                    retries += 1
                    continue
                else:
                    self.stdout.write(self.style.ERROR("Could not resolve Elasticsearch hostname"))
                    return
            
            try:
                # Try a simple request to check if Elasticsearch is up
                response = requests.get(f"http://{es_hosts[0]}", timeout=10)
                if response.status_code == 200:
                    connected = True
                    self.stdout.write(self.style.SUCCESS("Successfully connected to Elasticsearch"))
                else:
                    self.stdout.write(self.style.WARNING(f"Elasticsearch returned status code {response.status_code}"))
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
                error_msg = str(e)
                self.stdout.write(self.style.WARNING(f"Connection error: {error_msg}"))
                if wait:
                    self.stdout.write(f"Elasticsearch not available, retrying in {retry_interval} seconds... ({retries+1}/{max_retries})")
                    time.sleep(retry_interval)
                    retries += 1
                else:
                    self.stdout.write(self.style.ERROR("Could not connect to Elasticsearch"))
                    return
        
        if not connected:
            self.stdout.write(self.style.ERROR(f"Failed to connect to Elasticsearch after {max_retries} retries"))
            return
        
        # Create Elasticsearch client with timeout settings
        try:
            es = Elasticsearch(
                es_hosts,
                retry_on_timeout=True,
                timeout=30
            )
            # Verify connection is working
            if not es.ping():
                self.stdout.write(self.style.ERROR("Could not ping Elasticsearch"))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating Elasticsearch client: {str(e)}"))
            return
        
        # Check if indices exist and create them if they don't
        for index in registry.get_indices():
            index_name = index._name
            try:
                if not es.indices.exists(index=index_name):
                    self.stdout.write(f"Creating index '{index_name}'...")
                    registry.update_index(index)
                    self.stdout.write(self.style.SUCCESS(f"Successfully created index '{index_name}'"))
                else:
                    self.stdout.write(f"Index '{index_name}' already exists")
            except TransportError as e:
                self.stdout.write(self.style.ERROR(f"Transport error creating index '{index_name}': {str(e)}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating index '{index_name}': {str(e)}"))
        
        # Check if we need to populate the indices
        try:
            # Check if there are any documents in the indices
            empty_indices = []
            for index in registry.get_indices():
                index_name = index._name
                try:
                    count = es.count(index=index_name)['count']
                    if count == 0:
                        empty_indices.append(index_name)
                except TransportError as e:
                    self.stdout.write(self.style.ERROR(f"Transport error checking index '{index_name}': {str(e)}"))
                    empty_indices.append(index_name)  # Assume empty if we can't check
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error checking index '{index_name}': {str(e)}"))
                    empty_indices.append(index_name)  # Assume empty if we can't check
            
            if empty_indices:
                self.stdout.write(f"The following indices are empty or could not be checked: {', '.join(empty_indices)}")
                self.stdout.write("You may want to run 'python manage.py rebuild_elasticsearch_index' to populate them")
            else:
                self.stdout.write(self.style.SUCCESS("All indices contain documents"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error checking indices: {str(e)}"))
            self.stdout.write("You may want to run 'python manage.py rebuild_elasticsearch_index' to ensure indices are populated")
        
        self.stdout.write(self.style.SUCCESS("Elasticsearch initialization completed"))