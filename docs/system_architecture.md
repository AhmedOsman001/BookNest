# BookNest System Architecture

This document provides a detailed overview of the BookNest system architecture, including the key components and their interactions.

## Architecture Overview

BookNest follows a modern web application architecture with a Django REST Framework backend, PostgreSQL database, and various integrated services.

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

## Key Components

### Backend (Django REST Framework)

The backend is built using Django REST Framework and consists of the following main applications:

1. **Users App**
   - Custom user model and authentication
   - User profiles with social links and interests
   - JWT-based authentication

2. **Books App**
   - Book and author management
   - Reading lists
   - Ratings and reviews
   - Search functionality

3. **Follows App**
   - User follow relationships
   - Follower/following management

4. **Notifications App**
   - Generic notification system
   - Notification types and preferences

### Database (PostgreSQL)

PostgreSQL is used as the primary database, with models organized into the following categories:

1. **User-related Models**
   - CustomUser
   - Profile
   - ProfileInterest
   - ProfileSocialLink

2. **Book-related Models**
   - Book
   - Author
   - BookAuthor (junction table)
   - BookGenre
   - BookRating
   - BookReview

3. **Reading List Models**
   - ReadingList
   - ReadingListBooks (junction table)

4. **Social Models**
   - Follow
   - Notification
   - NotificationType

### Search (Elasticsearch)

Elasticsearch is integrated for powerful search capabilities:

- Book search by title, author, and description
- Fuzzy matching and relevance scoring
- Implemented through django-elasticsearch-dsl

### Media Storage (Cloudinary)

Cloudinary is used for storing and serving media files:

- Profile pictures
- Book cover images
- Automatic image transformations and optimizations

## Authentication Flow

1. User registers or logs in
2. Server validates credentials and issues JWT tokens (access and refresh)
3. Client includes access token in Authorization header for subsequent requests
4. Access token expires after 60 minutes
5. Client uses refresh token to obtain a new access token
6. On logout, tokens are blacklisted

## Request Flow

1. Client sends HTTP request to API endpoint
2. Django middleware processes the request
3. JWT authentication validates the token
4. Permission checks are performed
5. View handles the request and interacts with models
6. Response is serialized and returned to client

## Deployment Architecture

The application is containerized using Docker:

- Django application container
- PostgreSQL database container
- Nginx web server container for serving static files
- Docker Compose for orchestration

## Security Considerations

- JWT tokens for authentication
- Token blacklisting for logout
- CORS configuration for frontend access
- Secure password storage with Django's password hashing
- Environment-specific security settings