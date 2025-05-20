# BookNest Database Schema

This document provides a visual representation of the BookNest database schema, showing the relationships between different models in the system.

## Entity Relationship Diagram

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

## Key Relationships

### User Management
- **CustomUser** ↔ **Profile**: One-to-one relationship
- **Profile** ↔ **ProfileInterest**: One-to-many relationship
- **Profile** ↔ **ProfileSocialLink**: One-to-many relationship

### Book Management
- **Book** ↔ **Author**: Many-to-many relationship through BookAuthor
- **Book** ↔ **BookGenre**: One-to-many relationship
- **Book** ↔ **BookRating**: One-to-many relationship
- **Book** ↔ **BookReview**: One-to-many relationship

### Reading Lists
- **Profile** ↔ **ReadingList**: One-to-many relationship
- **ReadingList** ↔ **Book**: Many-to-many relationship through ReadingListBooks

### Social Features
- **Profile** ↔ **Follow**: One-to-many relationships (as both follower and followed)
- **CustomUser** ↔ **Notification**: One-to-many relationship (as recipient)

## Database Tables

| Model | Table Name | Description |
|-------|------------|-------------|
| CustomUser | auth_user | Extended Django user model |
| Profile | users_profile | User profile information |
| ProfileInterest | users_profileinterest | User interests |
| ProfileSocialLink | users_profilesociallink | User social media links |
| Book | book | Book information |
| Author | author | Author information |
| BookAuthor | author_books | Junction table for books and authors |
| BookGenre | book_genre | Book genres |
| ReadingList | Reading_List | User reading lists |
| ReadingListBooks | Reading_List_Books | Junction table for reading lists and books |
| BookRating | Book_Rating | User ratings for books |
| BookReview | Book_Review | User reviews for books |
| Follow | follows_follow | User follow relationships |
| Notification | notifications_notification | User notifications |
| NotificationType | notifications_notificationtype | Types of notifications |