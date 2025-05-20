import requests
import json
import time
import sys

def test_recommendation_trigger(base_url, email, password):
    """
    A test client that:
    1. Logs in as a user
    2. Creates ratings one by one up to 10
    3. Verifies recommendations are generated
    """
    # Create a session to maintain cookies/auth
    session = requests.Session()
    
    # Step 1: Login
    login_url = f"{base_url}/api/v1/users/login/"
    login_data = {"email": email, "password": password}
    
    try:
        login_response = session.post(login_url, json=login_data)
        login_response.raise_for_status()
        print(f"✅ Logged in as {email}")
    except Exception as e:
        print(f"❌ Login failed: {str(e)}")
        return False
    
    # Step 2: Get books to rate
    try:
        books_url = f"{base_url}/api/v1/books/list?limit=500"
        books_response = session.get(books_url)
        books_response.raise_for_status()
        
        books_data = books_response.json()
        if 'results' in books_data:
            books = books_data['results']
        else:
            books = books_data
            
        if not books or len(books) < 10:
            print(f"❌ Not enough books available. Found {len(books)}")
            return False
            
        print(f"✅ Found {len(books)} books to rate")
    except Exception as e:
        print(f"❌ Failed to get books: {str(e)}")
        return False
    
    # Step 3: Get current rating count
    try:
        user_ratings_url = f"{base_url}/api/v1/books/users/<str:user_id>/ratings"
        ratings_response = session.get(user_ratings_url)
        ratings_response.raise_for_status()
        
        ratings_data = ratings_response.json()
        
        if 'results' in ratings_data:
            current_ratings = len(ratings_data['results'])
        else:
            current_ratings = len(ratings_data)
            
        print(f"📊 User currently has {current_ratings} ratings")
        
        # Skip some ratings if user already has them
        ratings_needed = max(0, 10 - current_ratings)
        if ratings_needed == 0:
            print("👍 User already has 10+ ratings, checking recommendations...")
        else:
            print(f"📝 Need to create {ratings_needed} more ratings")
    except Exception as e:
        print(f"❌ Failed to get current ratings: {str(e)}")
        return False
    
    # Step 4: Create ratings one by one until we reach 10
    rating_url = f"{base_url}/api/v1/books/rating/create/"
    
    for i in range(ratings_needed):
        book = books[i]
        book_id = book.get('id')
        
        if not book_id:
            print(f"❌ Invalid book data: {book}")
            continue
            
        rating_data = {
            "book": book_id,
            "rate": 4  # Rating 4 out of 5
        }
        
        try:
            rate_response = session.post(rating_url, json=rating_data)
            rate_response.raise_for_status()
            current_ratings += 1
            print(f"⭐ Added rating #{current_ratings} for book {book_id}")
            
            # Small delay to avoid rate limits
            time.sleep(1)
        except Exception as e:
            print(f"❌ Failed to rate book {book_id}: {str(e)}")
    
    # Step 5: Check if we have recommendations
    print("\n🔍 Checking for recommendations...")
    time.sleep(3)  # Give the system a moment to process recommendations
    
    try:
        recommendations_url = f"{base_url}/api/v1/recommendation/user-recommendations/"
        recs_response = session.get(recommendations_url)
        recs_response.raise_for_status()
        
        recs_data = recs_response.json()
        
        if 'results' in recs_data:
            recommendations = recs_data['results']
        else:
            recommendations = recs_data
            
        rec_count = len(recommendations)
        
        if rec_count > 0:
            print(f"✅ Success! Found {rec_count} recommendations")
            print("\nTop 3 recommendations:")
            for i, rec in enumerate(recommendations[:3]):
                book_title = rec.get('book', {}).get('title', 'Unknown')
                score = rec.get('score', 0)
                print(f"  {i+1}. {book_title} (Score: {score:.2f})")
        else:
            print("⚠️ No recommendations found yet")
            
            # Try manually triggering recommendations
            print("\n🔄 Manually triggering recommendations...")
            trigger_url = f"{base_url}/api/v1/recommendation/trigger-recommendations/"
            trigger_response = session.post(trigger_url)
            
            if trigger_response.status_code == 200:
                print("✅ Successfully triggered recommendations")
                
                # Check again after a delay
                time.sleep(5)
                recs_response = session.get(recommendations_url)
                recs_data = recs_response.json()
                
                if 'results' in recs_data:
                    recommendations = recs_data['results']
                else:
                    recommendations = recs_data
                    
                rec_count = len(recommendations)
                if rec_count > 0:
                    print(f"✅ Success! Found {rec_count} recommendations after manual trigger")
                else:
                    print("❌ Still no recommendations found after manual trigger")
            else:
                print(f"❌ Failed to trigger recommendations: {trigger_response.text}")
    except Exception as e:
        print(f"❌ Failed to check recommendations: {str(e)}")
        
    return True

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python test_recommendation_trigger.py BASE_URL USERNAME PASSWORD")
        print("Example: python test_recommendation_trigger.py http://localhost:8000 testuser1 password123")
        sys.exit(1)
        
    base_url = sys.argv[1].rstrip('/')
    username = sys.argv[2]
    password = sys.argv[3]
    
    test_recommendation_trigger(base_url, username, password)