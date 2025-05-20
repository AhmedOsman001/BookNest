from tkinter import N
from rest_framework import serializers
from books.models import Book, Author, ReadingList, BookGenre, BookAuthor


class BookGenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookGenre
        fields = ["genre"]


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["author_id", "name", "bio" , "date_of_birth" , "number_of_books"]


class BookSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True)
    genres = serializers.ListField(child=serializers.CharField(), write_only=True)
    reviews_count = serializers.SerializerMethodField(read_only=True)
    # average_rate = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)

    class Meta:
        model = Book
        fields = [
            "isbn13",
            "isbn",
            "title",
            "authors",
            "genres",
            "average_rate",
            "description",
            "publication_date",
            "number_of_pages",
            "cover_img",
            "number_of_ratings",
            "reviews_count",
        ]
        
    def get_reviews_count(self, obj):
        return obj.reviews.count()


    
    def to_representation(self, instance):

        rep = super().to_representation(instance)
        # update the genres field to be a list of genres not dictionary of dictionaries
        rep["genres"] = list(
            BookGenre.objects.filter(book=instance).values_list("genre", flat=True)
        )
        return rep

    # def get_genres(self, obj):
    #     genres = BookGenre.objects.filter(book=obj).values_list("genre", flat=True)
    #     return list(genres)

    def create(self, validated_data):
        authors_data = validated_data.pop("authors") # pop authors data from validated data to use it in creating book authors through BookAuthor model
        genres_data = validated_data.pop("genres", []) # pop genres data from validated data to use it in creating book genres through BookGenre model
        book = Book.objects.create(**validated_data) # create the book instance with the rest of the validated data fields 

        for author_data in authors_data:
            author, created = Author.objects.get_or_create(**author_data) # get or create author instance from the author data 
            BookAuthor.objects.create(book=book, author=author) # create the book author instance with the book and author instances

        for genre in genres_data: 
            BookGenre.objects.create(book=book, genre=genre) 

        return book 

    def update(self, instance, validated_data):
        authors_data = validated_data.pop("authors" , None)
        genres_data = validated_data.pop("genres", None)

        instance.title = validated_data.get("title", instance.title)
        instance.description = validated_data.get("description", instance.description)
        instance.publication_date = validated_data.get(
            "publication_date", instance.publication_date
        )
        instance.number_of_pages = validated_data.get(
            "number_of_pages", instance.number_of_pages
        )
        instance.cover_img = validated_data.get("cover_img", instance.cover_img)
        instance.number_of_ratings = validated_data.get(
            "number_of_ratings", instance.number_of_ratings
        )
        instance.average_rate = validated_data.get(
            "average_rate", instance.average_rate
        )
        instance.save()

        if authors_data is not None:
            instance.authors.clear()
            for author_data in authors_data:
                author, created = Author.objects.get_or_create(**author_data)
                BookAuthor.objects.create(book=instance, author=author)

        if genres_data is not None:
            BookGenre.objects.filter(book=instance).delete()
            for genre in genres_data:
                BookGenre.objects.create(book=instance, genre=genre)

        return instance



class ReadingListSerializer(serializers.ModelSerializer):
    book_count = serializers.SerializerMethodField()
    owner_username = serializers.SerializerMethodField()
    
    class Meta:
        model = ReadingList
        fields = ["list_id", "name", "type", "privacy", "created_at", "book_count", "owner_username"]
        read_only_fields = ["list_id", "created_at", "book_count", "owner_username"]
    
    def get_book_count(self, obj):
        return obj.books.count()
    
    def get_owner_username(self, obj):
        return obj.profile.user.username if obj.profile and obj.profile.user else None


class ReadingListDetailSerializer(ReadingListSerializer):
    books = BookSerializer(many=True, read_only=True)

    class Meta(ReadingListSerializer.Meta):
        fields = ReadingListSerializer.Meta.fields + ["books"]
