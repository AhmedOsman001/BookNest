from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from books.models import Book, Author
from users.models import User  # Assuming you have a User model for authentication
from datetime import date

class BookAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.admin_user = User.objects.create_superuser(username='adminuser', password='adminpassword')

        self.author1 = Author.objects.create(name='Author One', date_of_birth=date(1970, 1, 1))
        self.book1 = Book.objects.create(
            isbn13='9780000000001',
            title='Test Book 1',
            publication_date=date(2020, 1, 1),
            number_of_pages=200
        )
        self.book1.authors.add(self.author1)

        self.book2 = Book.objects.create(
            isbn13='9780000000002',
            title='Test Book 2',
            publication_date=date(2021, 1, 1),
            number_of_pages=250
        )
        self.book2.authors.add(self.author1)

        self.book_list_url = reverse('book-list-api')
        self.book_detail_url = lambda pk: reverse('book-detail-api', kwargs={'pk': pk})
        self.book_create_url = reverse('book-create')
        self.book_update_url = lambda pk: reverse('book-update', kwargs={'pk': pk})
        self.book_delete_url = lambda pk: reverse('book-delete', kwargs={'pk': pk})

    def test_get_book_list_unauthenticated(self):
        response = self.client.get(self.book_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2) # Assuming LimitOffsetPagination

    def test_get_book_detail_unauthenticated(self):
        response = self.client.get(self.book_detail_url(self.book1.isbn13))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.book1.title)

    def test_create_book_unauthenticated(self):
        data = {
            'isbn13': '9780000000003',
            'title': 'New Book',
            'publication_date': '2022-01-01',
            'number_of_pages': 150,
            'authors': [self.author1.author_id]
        }
        response = self.client.post(self.book_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) # or 403 if IsAuthenticated is used without IsAdminUser

    def test_create_book_authenticated_admin(self):
        self.client.login(username='adminuser', password='adminpassword')
        data = {
            'isbn13': '9780000000003',
            'title': 'New Book by Admin',
            'publication_date': '2022-01-01',
            'number_of_pages': 150,
            'authors': [self.author1.author_id]
        }
        response = self.client.post(self.book_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 3)
        self.assertEqual(Book.objects.get(isbn13='9780000000003').title, 'New Book by Admin')

    def test_update_book_authenticated_admin(self):
        self.client.login(username='adminuser', password='adminpassword')
        updated_data = {'title': 'Updated Test Book 1'}
        response = self.client.patch(self.book_update_url(self.book1.isbn13), updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book1.refresh_from_db()
        self.assertEqual(self.book1.title, 'Updated Test Book 1')

    def test_delete_book_authenticated_admin(self):
        self.client.login(username='adminuser', password='adminpassword')
        response = self.client.delete(self.book_delete_url(self.book1.isbn13))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Book.objects.count(), 1)

class AuthorAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.admin_user = User.objects.create_superuser(username='adminuser', password='adminpassword')

        self.author1 = Author.objects.create(name='Author Alpha', bio='Bio Alpha', date_of_birth=date(1980, 5, 5))
        self.author2 = Author.objects.create(name='Author Beta', bio='Bio Beta', date_of_birth=date(1990, 6, 6))

        self.author_list_url = reverse('authors-list-api')
        self.author_detail_url = lambda pk: reverse('author-detail-api', kwargs={'pk': pk})
        self.author_create_url = reverse('author-create')
        self.author_update_url = lambda pk: reverse('author-update', kwargs={'pk': pk})
        self.author_delete_url = lambda pk: reverse('author-delete', kwargs={'pk': pk})

    def test_get_author_list_unauthenticated(self):
        response = self.client.get(self.author_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_author_detail_unauthenticated(self):
        response = self.client.get(self.author_detail_url(self.author1.author_id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.author1.name)

    def test_create_author_unauthenticated(self):
        data = {'name': 'New Author', 'bio': 'New Bio', 'date_of_birth': '2000-01-01'}
        response = self.client.post(self.author_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_author_authenticated_admin(self):
        self.client.login(username='adminuser', password='adminpassword')
        data = {'name': 'New Author Admin', 'bio': 'New Bio Admin', 'date_of_birth': '2001-01-01'}
        response = self.client.post(self.author_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Author.objects.count(), 3)
        self.assertEqual(Author.objects.get(name='New Author Admin').bio, 'New Bio Admin')

    def test_update_author_authenticated_admin(self):
        self.client.login(username='adminuser', password='adminpassword')
        updated_data = {'name': 'Updated Author Alpha'}
        response = self.client.patch(self.author_update_url(self.author1.author_id), updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.author1.refresh_from_db()
        self.assertEqual(self.author1.name, 'Updated Author Alpha')

    def test_delete_author_authenticated_admin(self):
        self.client.login(username='adminuser', password='adminpassword')
        response = self.client.delete(self.author_delete_url(self.author1.author_id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Author.objects.count(), 1)

    def test_get_author_books_by_id(self):
        book = Book.objects.create(isbn13='9781111111111', title='Book by Alpha')
        book.authors.add(self.author1)
        url = reverse('author-books-by-id', kwargs={'pk': self.author1.author_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Book by Alpha')

    def test_get_author_books_by_name(self):
        book = Book.objects.create(isbn13='9782222222222', title='Another Book by Alpha')
        book.authors.add(self.author1)
        url = reverse('author-books-by-name', kwargs={'name': self.author1.name})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1) # Assumes only one book by this author for this test
        self.assertEqual(response.data['results'][0]['title'], 'Another Book by Alpha')

# Add tests for BookReview, BookRating, ReadingList API endpoints similarly
# Remember to handle authentication and permissions for each endpoint