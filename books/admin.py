from django.contrib import admin
# Register your models here.
from .models import Book, Author, BookGenre, BookAuthor, ReadingList, ReadingListBooks, BookRating, BookReview
from users.models import Profile , ProfileInterest , ProfileSocialLink , CustomUser
from follows.models import Follow
from notifications.models import Notification , NotificationType

admin.site.register(Book)
admin.site.register(Author)
admin.site.register(BookGenre)
admin.site.register(BookAuthor)
admin.site.register(ReadingList)
admin.site.register(ReadingListBooks)
admin.site.register(BookRating)
admin.site.register(BookReview)
admin.site.register(Profile)
admin.site.register(ProfileInterest)
admin.site.register(ProfileSocialLink)
admin.site.register(Follow)
admin.site.register(CustomUser)
admin.site.register(Notification)
admin.site.register(NotificationType)