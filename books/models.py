from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from users.models.profile import Profile
import manage


class Author(models.Model):

    author_id = models.AutoField(primary_key=True)
    name = models.TextField()
    number_of_books = models.SmallIntegerField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'author'

    def __str__(self):
        return self.name

class Book(models.Model):

    isbn13 = models.CharField(primary_key=True, max_length=13)
    isbn = models.CharField(max_length=10, null=True, blank=True)
    cover_img = models.URLField(null=True, blank=True)
    title = models.TextField(null=False)
    description = models.TextField(null=True, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    number_of_pages = models.IntegerField(null=True, blank=True)
    number_of_ratings = models.IntegerField(default=0)
    average_rate = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True
    )
    authors = models.ManyToManyField('books.Author' , related_name='books' , through='BookAuthor')

    # objects = BookManager()
    

    class Meta:
        db_table = "book"
    
    def __str__(self):
        return self.title


class BookAuthor(models.Model):
    id = models.AutoField(primary_key=True)
    book = models.ForeignKey(
        'books.Book', 
        on_delete=models.CASCADE,
        db_column='book_id'
    )
    author = models.ForeignKey(
        'books.Author',
        on_delete=models.CASCADE,
        db_column='author_id'
    )

    class Meta:
        db_table = 'author_books'
        unique_together = ('book', 'author')
        ordering = ['-id']

    def __str__(self):
        return self.author.name

class BookGenre(models.Model):
    id = models.AutoField(primary_key=True)

    book = models.ForeignKey(
        'books.Book',
        on_delete=models.CASCADE,
        db_column='isbn13'
        , related_name='genres'
    )
    genre = models.TextField(max_length=255)

    class Meta:
        db_table = 'book_genre'
    
    def __str__(self):
        return self.genre

class ReadingList(models.Model):

  
    LIST_PRIVACY = (
        ('public', 'Public'),
        ('private', 'Private'),
    )

    LIST_TYPES = (
        ('todo', 'To Do'),
        ('doing', 'Doing'),
        ('done', 'Done'),
        ('custom', 'Custom'),
    )

    list_id = models.AutoField(primary_key=True)
    name = models.TextField()

    books = models.ManyToManyField('books.Book', through='ReadingListBooks')

    type = models.CharField(
        max_length=10,
        choices=LIST_TYPES,
    )
    privacy = models.CharField(
        max_length=10,
        choices=LIST_PRIVACY,
        default='public'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    profile = models.ForeignKey(
        'users.Profile',
        on_delete=models.CASCADE,
        related_name='reading_lists'
    )

    class Meta:
        db_table = 'Reading_List'

    def __str__(self):
        return self.name

class ReadingListBooks(models.Model):

    id = models.AutoField(primary_key=True)

    readinglist = models.ForeignKey(
        'books.ReadingList',
        on_delete=models.CASCADE,
        related_name='reading_list_books'
    )
    book = models.ForeignKey(
        'books.Book',
        on_delete=models.CASCADE,
        related_name='reading_list_books'
    )

    class Meta:
        db_table = 'Reading_List_Books'
        
    def __str__(self):
        return self.book.title

class BookRating(models.Model):

    rate_id = models.AutoField(primary_key=True)
    average_rate = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True
    )
    rate = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5)
        ]
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    book = models.ForeignKey(
        'books.Book',
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'Book_Rating'
        unique_together = ('user', 'book')

    def __str__(self):
        return f'{self.user.username} rated {self.book.title} with {self.rate}'
    
    
class BookReview(models.Model):
    review_id = models.AutoField(primary_key=True)
    review_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)
    # likes_count = models.IntegerField(default=0)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    book = models.ForeignKey(
        'books.Book',
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    class Meta:
        db_table = 'Book_Review'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} review for {self.book.title}'






