from django.test import TestCase
from django.core.exceptions import ValidationError
from books.models import Author, Book, BookAuthor, BookGenre, ReadingList, BookRating, BookReview
from users.models import CustomUser
from datetime import date

class AuthorModelTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(
            name="Test Author",
            bio="A test bio",
            date_of_birth=date(1980, 1, 1)
        )

    def test_author_creation(self):
        self.assertEqual(self.author.name, "Test Author")
        self.assertEqual(self.author.bio, "A test bio")
        self.assertEqual(self.author.date_of_birth, date(1980, 1, 1))
        self.assertIsNone(self.author.number_of_books)

    def test_author_str(self):
        self.assertEqual(str(self.author), "Test Author")

class BookModelTests(TestCase):
    def setUp(self):
        self.author1 = Author.objects.create(name="Author One")
        self.author2 = Author.objects.create(name="Author Two")
        self.book = Book.objects.create(
            isbn13="9780000000001",
            title="Test Book",
            description="A description for the test book.",
            publication_date=date(2023, 1, 1),
            number_of_pages=300,
            average_rate=4.50
        )
        self.book.authors.add(self.author1, through_defaults={})
        self.book.authors.add(self.author2, through_defaults={})

    def test_book_creation(self):
        self.assertEqual(self.book.isbn13, "9780000000001")
        self.assertEqual(self.book.title, "Test Book")
        self.assertEqual(self.book.description, "A description for the test book.")
        self.assertEqual(self.book.publication_date, date(2023, 1, 1))
        self.assertEqual(self.book.number_of_pages, 300)
        self.assertEqual(self.book.average_rate, 4.50)
        self.assertEqual(self.book.number_of_ratings, 0)

    def test_book_str(self):
        self.assertEqual(str(self.book), "Test Book")

    def test_book_authors_relationship(self):
        self.assertEqual(self.book.authors.count(), 2)
        self.assertIn(self.author1, self.book.authors.all())
        self.assertIn(self.author2, self.book.authors.all())

class BookAuthorModelTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(name="Test Author")
        self.book = Book.objects.create(isbn13="9780000000002", title="Another Test Book")
        self.book_author = BookAuthor.objects.create(book=self.book, author=self.author)

    def test_book_author_creation(self):
        self.assertEqual(self.book_author.book, self.book)
        self.assertEqual(self.book_author.author, self.author)

    def test_book_author_str(self):
        self.assertEqual(str(self.book_author), "Test Author")

from django.test import TestCase, override_settings
from books.models import BookGenre

@override_settings(ELASTICSEARCH_DSL_SIGNAL_PROCESSOR='django_elasticsearch_dsl.signals.RealTimeSignalProcessor',
                  ELASTICSEARCH_DSL_AUTOSYNC=False)
class BookGenreModelTests(TestCase):
    def test_book_genre_creation(self):
        self.assertEqual(self.book_genre.book, self.book)
        self.assertEqual(self.book_genre.genre, "Fiction")

    def test_book_genre_str(self):
        self.assertEqual(str(self.book_genre), "Fiction")

# Add tests for ReadingList, BookRating, BookReview similarly
# Remember to create User and Profile instances where necessary for ForeignKey relationships
