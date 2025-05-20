from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from books.models import Book, Author, BookAuthor, BookGenre
from django_elasticsearch_dsl.registries import registry


@receiver(post_save, sender=Book)
def update_book_in_elasticsearch(sender, instance, **kwargs):
    """
    Update the Elasticsearch index when a book is created or updated.
    """
    try:
        registry.update(instance)
    except Exception as e:
        # Log the error but don't raise it to prevent disrupting the save operation
        print(f"Error updating Elasticsearch index for book {instance.isbn13}: {e}")


@receiver(post_delete, sender=Book)
def delete_book_from_elasticsearch(sender, instance, **kwargs):
    """
    Delete the book from the Elasticsearch index when it's deleted from the database.
    """
    try:
        registry.delete(instance)
    except Exception as e:
        # Log the error
        print(f"Error deleting book {instance.isbn13} from Elasticsearch index: {e}")


@receiver(post_save, sender=Author)
def update_author_books_in_elasticsearch(sender, instance, **kwargs):
    """
    Update all books by this author in the Elasticsearch index.
    """
    try:
        # Get all books by this author
        book_authors = BookAuthor.objects.filter(author=instance)
        for book_author in book_authors:
            registry.update(book_author.book)
    except Exception as e:
        print(f"Error updating Elasticsearch index for books by author {instance.name}: {e}")


@receiver(post_save, sender=BookAuthor)
@receiver(post_delete, sender=BookAuthor)
def update_book_author_in_elasticsearch(sender, instance, **kwargs):
    """
    Update the book in Elasticsearch when a book-author relationship is created or deleted.
    """
    try:
        registry.update(instance.book)
    except Exception as e:
        print(f"Error updating Elasticsearch index for book {instance.book.isbn13}: {e}")


@receiver(post_save, sender=BookGenre)
@receiver(post_delete, sender=BookGenre)
def update_book_genre_in_elasticsearch(sender, instance, **kwargs):
    """
    Update the book in Elasticsearch when a book-genre relationship is created or deleted.
    """
    try:
        registry.update(instance.book)
    except Exception as e:
        print(f"Error updating Elasticsearch index for book {instance.book.isbn13}: {e}")