# BookNest API Endpoints Documentation

This document provides detailed information about all API endpoints available in the BookNest application.

## Table of Contents

1. [Authentication](#authentication)
2. [User Profiles](#user-profiles)
3. [Books](#books)
4. [Authors](#authors)
5. [Reading Lists](#reading-lists)
6. [Ratings and Reviews](#ratings-and-reviews)
7. [Follow System](#follow-system)
8. [Notifications](#notifications)

## Authentication

### Register a new user

```http
POST /api/v1/users/register/
```

**Request Body:**

```json
{
  "username": "string",
  "email": "string",
  "password1": "string",
  "password2": "string"
}
```

**Response:**

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "user": {
    "pk": "integer",
    "username": "string",
    "email": "string"
  }
}
```

### Login

```http
POST /api/v1/users/login/
```

**Request Body:**

```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "user": {
    "pk": "integer",
    "username": "string",
    "email": "string"
  }
}
```

### Logout

```http
POST /api/v1/users/logout/
```

**Request Body:**

```json
{
  "refresh_token": "string"
}
```

**Response:**

```json
{
  "detail": "Successfully logged out."
}
```

### Get Current User

```http
GET /api/v1/users/user/
```

**Response:**

```json
{
  "pk": "integer",
  "username": "string",
  "email": "string"
}
```

### Verify Token

```http
POST /api/v1/users/token/verify/
```

**Request Body:**

```json
{
  "token": "string"
}
```

### Refresh Token

```http
POST /api/v1/users/token/refresh/
```

**Request Body:**

```json
{
  "refresh": "string"
}
```

**Response:**

```json
{
  "access": "string"
}
```

## User Profiles

### List All Profiles

```http
GET /api/v1/users/profile/
```

### Get Profile Details

```http
GET /api/v1/users/profile/{id}/
```

### Get Current User's Profile

```http
GET /api/v1/users/profile/me/
```

**Response:**

```json
{
  "id": "integer",
  "user": {
    "id": "integer",
    "username": "string",
    "email": "string"
  },
  "profile_pic": "string",
  "bio": "string",
  "profile_type": "string",
  "interests": [
    {
      "id": "integer",
      "interest": "string"
    }
  ],
  "social_links": [
    {
      "id": "integer",
      "platform": "string",
      "url": "string"
    }
  ],
  "created_at": "string",
  "updated_at": "string"
}
```

### Update Current User's Profile

```http
PATCH /api/v1/users/profile/me/
```

**Request Body:**

```json
{
  "bio": "string",
  "profile_type": "string"
}
```

### Upload Profile Picture

```http
POST /api/v1/users/profiles/upload-picture/
```

**Request Body:**

Multipart form data with `profile_pic` field containing the image file.

## Books

### List All Books

```http
GET /api/v1/books/list/
```

**Query Parameters:**

- `page`: Page number for pagination
- `page_size`: Number of items per page

**Response:**

```json
{
  "count": "integer",
  "next": "string",
  "previous": "string",
  "results": [
    {
      "isbn13": "string",
      "title": "string",
      "cover_img": "string",
      "authors": [
        {
          "author_id": "integer",
          "name": "string"
        }
      ],
      "average_rate": "number"
    }
  ]
}
```

### Search Books

```http
GET /api/v1/books/search/
```

**Query Parameters:**

- `q`: Search query
- `page`: Page number for pagination
- `page_size`: Number of items per page

### Get Book Suggestions

```http
GET /api/v1/books/suggestions/
```

### Get Book Details

```http
GET /api/v1/books/{isbn13}/
```

**Response:**

```json
{
  "isbn13": "string",
  "isbn": "string",
  "title": "string",
  "description": "string",
  "cover_img": "string",
  "publication_date": "string",
  "number_of_pages": "integer",
  "number_of_ratings": "integer",
  "average_rate": "number",
  "authors": [
    {
      "author_id": "integer",
      "name": "string"
    }
  ],
  "genres": [
    {
      "id": "integer",
      "genre": "string"
    }
  ]
}
```

### Create Book

```http
POST /api/v1/books/create/
```

**Request Body:**

```json
{
  "isbn13": "string",
  "isbn": "string",
  "title": "string",
  "description": "string",
  "cover_img": "string",
  "publication_date": "string",
  "number_of_pages": "integer",
  "authors": ["integer"],
  "genres": ["string"]
}
```

### Update Book

```http
PUT /api/v1/books/{isbn13}/update/
```

### Delete Book

```http
DELETE /api/v1/books/{isbn13}/delete/
```

## Authors

### List All Authors

```http
GET /api/v1/books/authors/
```

### Get Author Details

```http
GET /api/v1/books/authors/{id}/
```

**Response:**

```json
{
  "author_id": "integer",
  "name": "string",
  "bio": "string",
  "date_of_birth": "string",
  "number_of_books": "integer"
}
```

### Get Books by Author

```http
GET /api/v1/books/authors/{id}/books/
```

### Create Author

```http
POST /api/v1/books/authors/create/
```

**Request Body:**

```json
{
  "name": "string",
  "bio": "string",
  "date_of_birth": "string"
}
```

### Update Author

```http
PUT /api/v1/books/authors/{id}/update/
```

### Delete Author

```http
DELETE /api/v1/books/authors/{id}/delete/
```

## Reading Lists

### List User's Reading Lists

```http
GET /api/v1/books/reading-lists/
```

**Response:**

```json
[
  {
    "list_id": "integer",
    "name": "string",
    "type": "string",
    "privacy": "string",
    "created_at": "string",
    "books_count": "integer"
  }
]
```

### Get Reading List Details

```http
GET /api/v1/books/reading-lists/{id}/
```

**Response:**

```json
{
  "list_id": "integer",
  "name": "string",
  "type": "string",
  "privacy": "string",
  "created_at": "string",
  "books": [
    {
      "isbn13": "string",
      "title": "string",
      "cover_img": "string"
    }
  ]
}
```

### Create Reading List

```http
POST /api/v1/books/reading-lists/create/
```

**Request Body:**

```json
{
  "name": "string",
  "type": "string",
  "privacy": "string"
}
```

### Update Reading List

```http
PUT /api/v1/books/reading-lists/{id}/update/
```

### Delete Reading List

```http
DELETE /api/v1/books/reading-lists/{id}/delete/
```

### Add/Remove Books from Reading List

```http
POST /api/v1/books/reading-lists/{id}/books/
```

**Request Body:**

```json
{
  "operation": "string", // "add" or "remove"
  "book_id": "string"
}
```

## Ratings and Reviews

### List All Ratings

```http
GET /api/v1/books/ratings/
```

### Get Rating Details

```http
GET /api/v1/books/ratings/{id}/
```

### Create Rating

```http
POST /api/v1/books/ratings/create/
```

**Request Body:**

```json
{
  "book": "string",
  "rate": "number"
}
```

### Update Rating

```http
PUT /api/v1/books/ratings/{id}/update/
```

### Delete Rating

```http
DELETE /api/v1/books/ratings/{id}/delete/
```

### Get Ratings for a Book

```http
GET /api/v1/books/{isbn13}/ratings/
```

### Get Ratings by Current User

```http
GET /api/v1/books/ratings/user/
```

### List All Reviews

```http
GET /api/v1/books/reviews/
```

### Get Review Details

```http
GET /api/v1/books/reviews/{id}/
```

### Create Review

```http
POST /api/v1/books/reviews/create/
```

**Request Body:**

```json
{
  "book": "string",
  "review_text": "string"
}
```

### Update Review

```http
PUT /api/v1/books/reviews/{id}/update/
```

### Delete Review

```http
DELETE /api/v1/books/reviews/{id}/delete/
```

### Get Reviews for a Book

```http
GET /api/v1/books/{isbn13}/reviews/
```

## Follow System

### List All Follows

```http
GET /api/v1/follow/
```

### Follow a User

```http
POST /api/v1/follow/create/
```

**Request Body:**

```json
{
  "followed": "integer"
}
```

### Get Follow Details

```http
GET /api/v1/follow/{id}/
```

### Unfollow a User

```http
DELETE /api/v1/follow/unfollow/{followed_id}/
```

### Get Current User's Followers

```http
GET /api/v1/follow/followers/
```

### Get Users Followed by Current User

```http
GET /api/v1/follow/following/
```

### Get a User's Followers

```http
GET /api/v1/follow/user/{user_id}/followers/
```

### Get Users Followed by a User

```http
GET /api/v1/follow/user/{user_id}/following/
```

## Notifications

### List User's Notifications

```http
GET /api/v1/notifications/
```

**Response:**

```json
{
  "count": "integer",
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": "integer",
      "recipient": {
        "id": "integer",
        "username": "string"
      },
      "actor": {
        "id": "integer",
        "username": "string"
      },
      "verb": "string",
      "target": "object",
      "read": "boolean",
      "timestamp": "string"
    }
  ]
}
```

### Get Notification Details

```http
GET /api/v1/notifications/{id}/
```

### Create Notification

```http
POST /api/v1/notifications/create/
```

### Update Notification

```http
PUT /api/v1/notifications/{id}/update/
```

### Delete Notification

```http
DELETE /api/v1/notifications/{id}/delete/
```

### Mark Notification as Read

```http
POST /api/v1/notifications/{id}/mark-read/
```

### Mark Notification as Unread

```http
POST /api/v1/notifications/{id}/mark-unread/
```

### Mark All Notifications as Read

```http
POST /api/v1/notifications/mark-all-read/
```

### Get Count of Unread Notifications

```http
GET /api/v1/notifications/unread-count/
```

**Response:**

```json
{
  "count": "integer"
}
```

### List Notification Types

```http
GET /api/v1/notifications/types/
```

### Get Notification Type Details

```http
GET /api/v1/notifications/types/{id}/
```