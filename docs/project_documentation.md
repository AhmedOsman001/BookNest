# BookNest Project Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [System Architecture](#system-architecture)
3. [Database Schema](#database-schema)
4. [Authentication System](#authentication-system)
5. [API Endpoints](#api-endpoints)
6. [Examples](#examples)

## System Overview

BookNest is a comprehensive book management platform built with Django REST Framework and PostgreSQL. The system allows users to discover books, create reading lists, follow other users, rate and review books, and receive notifications about relevant activities.

## System Architecture

BookNest follows a modern web application architecture with the following components:

### Backend

- **Framework**: Django REST Framework (DRF)
- **Database**: PostgreSQL
- **Authentication**: JWT (JSON Web Tokens)
- **Search**: Elasticsearch
- **File Storage**: Cloudinary

### Key Components

1. **User Management**
   - Custom user model with profile management
   - Authentication using JWT tokens
   - User profiles with social links and interests

2. **Book Management**
   - Book and author data models
   - Reading lists (public/private)
   - Ratings and reviews

3. **Social Features**
   - Follow system for users
   - Notification system

4. **Search and Discovery**
   - Book search functionality
   - Book suggestions

### Architecture Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Client         │────▶│  Django REST    │────▶│  PostgreSQL     │
│  Application    │◀────│  Framework API  │◀────│  Database       │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │      ▲
                              │      │
                              ▼      │
                        ┌─────────────────┐
                        │                 │
                        │  Elasticsearch  │
                        │  (Search)       │
                        │                 │
                        └─────────────────┘
                              │      ▲
                              │      │
                              ▼      │
                        ┌─────────────────┐
                        │                 │
                        │  Cloudinary     │
                        │  (Media Storage)│
                        │                 │
                        └─────────────────┘
```

## Database Schema

### User Models

#### CustomUser
- Extends Django's AbstractUser
- Managed by CustomUserManager
- Handles token management on deletion

#### Profile
- One-to-one relationship with CustomUser
- Stores user bio, profile picture, and profile type
- Profile types: Regular, Author, Publisher
- Stores user settings as JSON
- Related models: ProfileInterest, ProfileSocialLink

### Book Models

#### Book
- Primary key: isbn13
- Fields: title, description, cover_img, publication_date, number_of_pages, etc.
- Many-to-many relationship with Author through BookAuthor
- Related models: BookGenre, BookRating, BookReview

#### Author
- Fields: name, bio, date_of_birth, number_of_books
- Many-to-many relationship with Book through BookAuthor

#### ReadingList
- Fields: name, type, privacy, created_at
- Types: todo, doing, done, custom
- Privacy: public, private
- Many-to-many relationship with Book through ReadingListBooks

### Social Models

#### Follow
- Fields: follower, followed, created_at
- Represents follow relationships between users
- Prevents users from following themselves

#### Notification
- Generic notification system using ContentType framework
- Fields: recipient, actor, verb, target, action_object, notification_type
- Supports marking notifications as read/unread

### Database Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  CustomUser     │     │  Profile        │     │  ProfileInterest│
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│  id             │─┐   │  id             │─┐   │  id             │
│  username       │ │   │  user_id        │◀┘   │  profile_id     │
│  email          │ └──▶│  profile_pic    │     │  interest       │
│  password       │     │  bio            │     └─────────────────┘
└─────────────────┘     │  profile_type   │     
                        │  settings       │     ┌─────────────────┐
                        └─────────────────┘     │ProfileSocialLink│
                                                ├─────────────────┤
┌─────────────────┐     ┌─────────────────┐     │  id             │
│  Book           │     │  Author         │     │  profile_id     │
├─────────────────┤     ├─────────────────┤     │  platform       │
│  isbn13         │◀┐   │  author_id      │◀┐   │  url            │
│  title          │ │   │  name           │ │   └─────────────────┘
│  description    │ │   │  bio            │ │   
│  cover_img      │ │   │  date_of_birth  │ │   ┌─────────────────┐
│  pub_date       │ │   └─────────────────┘ │   │  Follow         │
└─────────────────┘ │                       │   ├─────────────────┤
                     │   ┌─────────────────┐│   │  id             │
┌─────────────────┐  │   │  BookAuthor    ││   │  follower_id    │
│  BookGenre      │  │   ├─────────────────┤│   │  followed_id    │
├─────────────────┤  │   │  id             ││   │  created_at     │
│  id             │  │   │  book_id        │┘   └─────────────────┘
│  book_id        │──┘   │  author_id      │    
│  genre          │      └─────────────────┘    ┌─────────────────┐
└─────────────────┘                             │  Notification   │
                        ┌─────────────────┐     ├─────────────────┤
┌─────────────────┐     │  ReadingList   │     │  id             │
│  BookRating     │     ├─────────────────┤     │  recipient_id   │
├─────────────────┤     │  list_id        │     │  actor_content  │
│  rate_id        │     │  name           │     │  target_content │
│  book_id        │◀┐   │  type           │     │  verb           │
│  user_id        │ │   │  privacy        │     │  read           │
│  rate           │ │   │  profile_id     │     │  timestamp      │
└─────────────────┘ │   └─────────────────┘     └─────────────────┘
                     │           │                
┌─────────────────┐  │           │                
│  BookReview     │  │           ▼                
├─────────────────┤  │   ┌─────────────────┐     
│  review_id      │  │   │ReadingListBooks │     
│  book_id        │◀─┘   ├─────────────────┤     
│  user_id        │      │  id             │     
│  review_text    │      │  readinglist_id │     
│  created_at     │      │  book_id        │     
└─────────────────┘      └─────────────────┘     
```

## Authentication System

BookNest uses JWT (JSON Web Tokens) for authentication, implemented through the `dj-rest-auth` and `djangorestframework-simplejwt` packages.

### Key Features

- **Token-based Authentication**: Uses JWT tokens for secure authentication
- **Token Refresh**: Access tokens expire after 60 minutes, refresh tokens after 7 days
- **Token Blacklisting**: Supports blacklisting of tokens for logout functionality
- **Custom User Model**: Extends Django's AbstractUser for additional functionality

### Authentication Flow

1. **Registration**: User registers with username, email, and password
2. **Login**: User logs in and receives access and refresh tokens
3. **Token Usage**: Access token is included in Authorization header for API requests
4. **Token Refresh**: Refresh token is used to obtain a new access token when it expires
5. **Logout**: Tokens are blacklisted on logout

## API Endpoints

### Authentication Endpoints

- `POST /api/v1/users/register/` - Register a new user
- `POST /api/v1/users/login/` - Login and receive tokens
- `POST /api/v1/users/logout/` - Logout and blacklist tokens
- `GET /api/v1/users/user/` - Get current user details
- `POST /api/v1/users/token/verify/` - Verify token validity
- `POST /api/v1/users/token/refresh/` - Refresh access token

### User Profile Endpoints

- `GET /api/v1/users/profile/` - List all profiles
- `GET /api/v1/users/profile/<id>/` - Get profile details
- `GET /api/v1/users/profile/me/` - Get current user's profile
- `PATCH /api/v1/users/profile/me/` - Update current user's profile
- `POST /api/v1/users/profiles/upload-picture/` - Upload profile picture

### Book Endpoints

- `GET /api/v1/books/list/` - List all books
- `GET /api/v1/books/search/` - Search for books
- `GET /api/v1/books/suggestions/` - Get book suggestions
- `GET /api/v1/books/<isbn13>/` - Get book details
- `POST /api/v1/books/create/` - Create a new book
- `PUT /api/v1/books/<isbn13>/update/` - Update a book
- `DELETE /api/v1/books/<isbn13>/delete/` - Delete a book

### Author Endpoints

- `GET /api/v1/books/authors/` - List all authors
- `GET /api/v1/books/authors/<id>/` - Get author details
- `GET /api/v1/books/authors/<id>/books/` - Get books by an author
- `POST /api/v1/books/authors/create/` - Create a new author
- `PUT /api/v1/books/authors/<id>/update/` - Update an author
- `DELETE /api/v1/books/authors/<id>/delete/` - Delete an author

### Reading List Endpoints

- `GET /api/v1/books/reading-lists/` - List user's reading lists
- `GET /api/v1/books/reading-lists/<id>/` - Get reading list details
- `POST /api/v1/books/reading-lists/create/` - Create a new reading list
- `PUT /api/v1/books/reading-lists/<id>/update/` - Update a reading list
- `DELETE /api/v1/books/reading-lists/<id>/delete/` - Delete a reading list
- `POST /api/v1/books/reading-lists/<id>/books/` - Add/remove books from reading list

### Rating and Review Endpoints

- `GET /api/v1/books/ratings/` - List all ratings
- `GET /api/v1/books/ratings/<id>/` - Get rating details
- `POST /api/v1/books/ratings/create/` - Create a new rating
- `PUT /api/v1/books/ratings/<id>/update/` - Update a rating
- `DELETE /api/v1/books/ratings/<id>/delete/` - Delete a rating
- `GET /api/v1/books/<isbn13>/ratings/` - Get ratings for a book
- `GET /api/v1/books/ratings/user/` - Get ratings by current user

- `GET /api/v1/books/reviews/` - List all reviews
- `GET /api/v1/books/reviews/<id>/` - Get review details
- `POST /api/v1/books/reviews/create/` - Create a new review
- `PUT /api/v1/books/reviews/<id>/update/` - Update a review
- `DELETE /api/v1/books/reviews/<id>/delete/` - Delete a review
- `GET /api/v1/books/<isbn13>/reviews/` - Get reviews for a book

### Follow Endpoints

- `GET /api/v1/follow/` - List all follows
- `POST /api/v1/follow/create/` - Follow a user
- `GET /api/v1/follow/<id>/` - Get follow details
- `DELETE /api/v1/follow/unfollow/<followed_id>/` - Unfollow a user
- `GET /api/v1/follow/followers/` - Get current user's followers
- `GET /api/v1/follow/following/` - Get users followed by current user
- `GET /api/v1/follow/user/<user_id>/followers/` - Get a user's followers
- `GET /api/v1/follow/user/<user_id>/following/` - Get users followed by a user

### Notification Endpoints

- `GET /api/v1/notifications/` - List user's notifications
- `GET /api/v1/notifications/<id>/` - Get notification details
- `POST /api/v1/notifications/create/` - Create a notification
- `PUT /api/v1/notifications/<id>/update/` - Update a notification
- `DELETE /api/v1/notifications/<id>/delete/` - Delete a notification
- `POST /api/v1/notifications/<id>/mark-read/` - Mark notification as read
- `POST /api/v1/notifications/<id>/mark-unread/` - Mark notification as unread
- `POST /api/v1/notifications/mark-all-read/` - Mark all notifications as read
- `GET /api/v1/notifications/unread-count/` - Get count of unread notifications
- `GET /api/v1/notifications/types/` - List notification types
- `GET /api/v1/notifications/types/<id>/` - Get notification type details

## Examples

### Authentication

#### Register a new user

```http
POST /api/v1/users/register/
Content-Type: application/json

{
  "username": "bookworm",
  "email": "bookworm@example.com",
  "password1": "securepassword123",
  "password2": "securepassword123"
}
```

Response:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "pk": 1,
    "username": "bookworm",
    "email": "bookworm@example.com"
  }
}
```

#### Login

```http
POST /api/v1/users/login/
Content-Type: application/json

{
  "username": "bookworm",
  "password": "securepassword123"
}
```

Response:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "pk": 1,
    "username": "bookworm",
    "email": "bookworm@example.com"
  }
}
```

### Book Operations

#### Search for books

```http
GET /api/v1/books/search/?q=python
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

Response:

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "isbn13": "9781449355739",
      "title": "Learning Python",
      "cover_img": "https://example.com/covers/learning_python.jpg",
      "authors": [
        {
          "author_id": 1,
          "name": "Mark Lutz"
        }
      ],
      "average_rate": 4.5
    },
    {
      "isbn13": "9781617294433",
      "title": "Python in Practice",
      "cover_img": "https://example.com/covers/python_practice.jpg",
      "authors": [
        {
          "author_id": 2,
          "name": "Alex Martelli"
        }
      ],
      "average_rate": 4.2
    }
  ]
}
```

#### Create a reading list

```http
POST /api/v1/books/reading-lists/create/
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

{
  "name": "Python Books",
  "type": "custom",
  "privacy": "public"
}
```

Response:

```json
{
  "list_id": 1,
  "name": "Python Books",
  "type": "custom",
  "privacy": "public",
  "created_at": "2023-07-15T14:30:45Z",
  "books": []
}
```

#### Add a book to a reading list

```http
POST /api/v1/books/reading-lists/1/books/
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

{
  "operation": "add",
  "book_id": "9781449355739"
}
```

Response:

```json
{
  "list_id": 1,
  "name": "Python Books",
  "type": "custom",
  "privacy": "public",
  "created_at": "2023-07-15T14:30:45Z",
  "books": [
    {
      "isbn13": "9781449355739",
      "title": "Learning Python",
      "cover_img": "https://example.com/covers/learning_python.jpg"
    }
  ]
}
```

### Social Features

#### Follow a user

```http
POST /api/v1/follow/create/
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

{
  "followed": 2
}
```

Response:

```json
{
  "id": 1,
  "follower": {
    "id": 1,
    "username": "bookworm"
  },
  "followed": {
    "id": 2,
    "username": "booklover"
  },
  "created_at": "2023-07-15T15:20:30Z"
}
```

#### Get notifications

```http
GET /api/v1/notifications/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

Response:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "recipient": {
        "id": 2,
        "username": "booklover"
      },
      "actor": {
        "id": 1,
        "username": "bookworm"
      },
      "verb": "followed you",
      "read": false,
      "timestamp": "2023-07-15T15:20:35Z"
    }
  ]
}
```