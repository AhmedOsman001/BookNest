from django.test import TestCase
from django.db import IntegrityError
from users.models import User, Profile  # Assuming User and Profile models from your project
from follows.models import Follow

class FollowModelTests(TestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(username='user1', password='password1')
        self.user2 = User.objects.create_user(username='user2', password='password2')
        self.user3 = User.objects.create_user(username='user3', password='password3')

        # Create profiles if they are not created automatically by a signal
        # If Profile is created via a signal on User creation, this might not be needed
        # or might need adjustment based on your Profile model's fields.
        self.profile1, _ = Profile.objects.get_or_create(user=self.user1, defaults={'bio': 'Profile 1 Bio'})
        self.profile2, _ = Profile.objects.get_or_create(user=self.user2, defaults={'bio': 'Profile 2 Bio'})
        self.profile3, _ = Profile.objects.get_or_create(user=self.user3, defaults={'bio': 'Profile 3 Bio'})

    def test_follow_creation(self):
        follow = Follow.objects.create(follower=self.profile1, followed=self.profile2)
        self.assertEqual(follow.follower, self.profile1)
        self.assertEqual(follow.followed, self.profile2)
        self.assertIsNotNone(follow.created_at)
        self.assertEqual(str(follow), f"{self.profile1.user.username} follows {self.profile2.user.username}")

    def test_user_cannot_follow_themselves(self):
        # The model's save method should prevent this.
        # Depending on how you test, direct creation might bypass save method if not careful.
        # If save method returns None or raises an error, adjust test.
        # Here, we assume the save method is overridden to simply not save.
        initial_follow_count = Follow.objects.count()
        follow_attempt = Follow(follower=self.profile1, followed=self.profile1)
        follow_attempt.save() # This should not create a Follow record
        self.assertEqual(Follow.objects.count(), initial_follow_count)

        # If your save method raises an exception, you might test it like this:
        # with self.assertRaises(SomeException): # Replace SomeException with the actual one
        #     Follow.objects.create(follower=self.profile1, followed=self.profile1)

    def test_unique_together_constraint(self):
        # First follow is fine
        Follow.objects.create(follower=self.profile1, followed=self.profile2)
        # Second attempt to follow the same user should fail due to unique_together
        with self.assertRaises(IntegrityError):
            Follow.objects.create(follower=self.profile1, followed=self.profile2)

    def test_related_names(self):
        Follow.objects.create(follower=self.profile1, followed=self.profile2)
        Follow.objects.create(follower=self.profile1, followed=self.profile3)
        Follow.objects.create(follower=self.profile2, followed=self.profile1)

        self.assertEqual(self.profile1.following.count(), 2)
        self.assertIn(self.profile2, [f.followed for f in self.profile1.following.all()])
        self.assertIn(self.profile3, [f.followed for f in self.profile1.following.all()])

        self.assertEqual(self.profile1.followers.count(), 1)
        self.assertIn(self.profile2, [f.follower for f in self.profile1.followers.all()])

        self.assertEqual(self.profile2.following.count(), 1)
        self.assertEqual(self.profile2.followers.count(), 1)

    def test_follow_ordering(self):
        # Create follows at different times (implicitly by creation order)
        follow1 = Follow.objects.create(follower=self.profile1, followed=self.profile2)
        follow2 = Follow.objects.create(follower=self.profile2, followed=self.profile3)
        
        # Assuming default ordering is '-created_at'
        follows = Follow.objects.all()
        self.assertEqual(follows.first(), follow2) # Newest first
        self.assertEqual(follows.last(), follow1)  # Oldest last