 from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from users.models import User, Profile
from follows.models import Follow

class FollowAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='user1_follow_api', password='password1')
        self.profile1, _ = Profile.objects.get_or_create(user=self.user1, defaults={'bio': 'Profile 1 Bio API'})
        
        self.user2 = User.objects.create_user(username='user2_follow_api', password='password2')
        self.profile2, _ = Profile.objects.get_or_create(user=self.user2, defaults={'bio': 'Profile 2 Bio API'})

        self.user3 = User.objects.create_user(username='user3_follow_api', password='password3')
        self.profile3, _ = Profile.objects.get_or_create(user=self.user3, defaults={'bio': 'Profile 3 Bio API'})

        # URLs
        self.follow_create_url = reverse('follow-create')
        self.unfollow_url = lambda followed_id: reverse('follow-delete', kwargs={'followed_id': followed_id})
        self.follower_list_url = reverse('follower-list') # Lists followers of the authenticated user
        self.following_list_url = reverse('following-list') # Lists who the authenticated user is following
        self.user_followers_url = lambda user_id: reverse('user-followers', kwargs={'user_id': user_id})
        self.user_following_url = lambda user_id: reverse('user-following', kwargs={'user_id': user_id})

    def test_follow_user_unauthenticated(self):
        response = self.client.post(self.follow_create_url, {'followed_id': self.profile2.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_follow_user_authenticated(self):
        self.client.login(username='user1_follow_api', password='password1')
        response = self.client.post(self.follow_create_url, {'followed_id': self.profile2.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Follow.objects.filter(follower=self.profile1, followed=self.profile2).exists())

    def test_follow_user_already_following(self):
        self.client.login(username='user1_follow_api', password='password1')
        Follow.objects.create(follower=self.profile1, followed=self.profile2)
        response = self.client.post(self.follow_create_url, {'followed_id': self.profile2.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) # Assuming serializer validation handles this

    def test_follow_self_attempt(self):
        self.client.login(username='user1_follow_api', password='password1')
        response = self.client.post(self.follow_create_url, {'followed_id': self.profile1.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) # Assuming serializer validation
        self.assertFalse(Follow.objects.filter(follower=self.profile1, followed=self.profile1).exists())

    def test_unfollow_user_authenticated(self):
        self.client.login(username='user1_follow_api', password='password1')
        Follow.objects.create(follower=self.profile1, followed=self.profile2)
        self.assertTrue(Follow.objects.filter(follower=self.profile1, followed=self.profile2).exists())
        response = self.client.delete(self.unfollow_url(self.profile2.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Follow.objects.filter(follower=self.profile1, followed=self.profile2).exists())

    def test_unfollow_user_not_following(self):
        self.client.login(username='user1_follow_api', password='password1')
        response = self.client.delete(self.unfollow_url(self.profile2.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Or appropriate error for not found

    def test_get_my_followers_list_authenticated(self):
        # user2 follows user1
        Follow.objects.create(follower=self.profile2, followed=self.profile1)
        self.client.login(username='user1_follow_api', password='password1')
        response = self.client.get(self.follower_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['follower']['user']['username'], self.profile2.user.username)

    def test_get_my_following_list_authenticated(self):
        # user1 follows user2
        Follow.objects.create(follower=self.profile1, followed=self.profile2)
        self.client.login(username='user1_follow_api', password='password1')
        response = self.client.get(self.following_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['followed']['user']['username'], self.profile2.user.username)

    def test_get_user_followers_list_public(self):
        # user1 follows user3, user2 follows user3
        Follow.objects.create(follower=self.profile1, followed=self.profile3)
        Follow.objects.create(follower=self.profile2, followed=self.profile3)
        # No authentication needed for this endpoint as per typical design
        response = self.client.get(self.user_followers_url(self.profile3.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        follower_usernames = [item['follower']['user']['username'] for item in response.data['results']]
        self.assertIn(self.profile1.user.username, follower_usernames)
        self.assertIn(self.profile2.user.username, follower_usernames)

    def test_get_user_following_list_public(self):
        # user1 follows user2 and user3
        Follow.objects.create(follower=self.profile1, followed=self.profile2)
        Follow.objects.create(follower=self.profile1, followed=self.profile3)
        response = self.client.get(self.user_following_url(self.profile1.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        followed_usernames = [item['followed']['user']['username'] for item in response.data['results']]
        self.assertIn(self.profile2.user.username, followed_usernames)
        self.assertIn(self.profile3.user.username, followed_usernames)