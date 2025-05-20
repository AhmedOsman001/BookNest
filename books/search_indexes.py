from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from books.models import Book


@registry.register_document
class BookDocument(Document):
    """Elasticsearch document for Book model"""
    # Define fields to be indexed
    isbn13 = fields.KeywordField()
    isbn = fields.KeywordField()
    title = fields.TextField(
        fields={
            'raw': fields.KeywordField(),
            'suggest': fields.CompletionField(),
        }
    )
    description = fields.TextField()
    
    # Author names as a nested field
    authors = fields.NestedField(properties={
        'name': fields.TextField(fields={'raw': fields.KeywordField()}),
    })
    
    # Genres as a keyword field
    genres = fields.KeywordField(multi=True)
    
    class Index:
        # Name of the Elasticsearch index
        name = 'books'
        # Index settings
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
        }
    
    class Django:
        model = Book  # The model associated with this document
        
        # The fields of the model to be indexed
        fields = [
            'cover_img',
            'publication_date',
            'number_of_pages',
            'average_rate',
        ]
        
        # Related fields to include in the document
        related_models = ['authors', 'genres']
    
    def get_instances_from_related(self, related_instance):
        """Get Book instances related to the related model instance"""
        if related_instance.__class__.__name__ == 'Author':
            return related_instance.books.all()
        elif related_instance.__class__.__name__ == 'BookGenre':
            return [related_instance.book]
        return None
    
    def prepare_authors(self, instance):
        """Prepare the authors field"""
        return [{'name': author.name} for author in instance.authors.all()]
    
    def prepare_genres(self, instance):
        """Prepare the genres field"""
        return [genre.genre for genre in instance.genres.all()]