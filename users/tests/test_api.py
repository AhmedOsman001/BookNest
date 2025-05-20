from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from users.models.profile import Profile
from django.core.files.uploadedfile import SimpleUploadedFile
import os

User = get_user_model()

class UserAuthAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('custom_register')
        self.login_url = reverse('rest_login')
        self.logout_url = reverse('rest_logout')
        self.user_details_url = reverse('rest_user_details')
        self.token_verify_url = reverse('token_verify')
        self.token_refresh_url = reverse('token_refresh')

        self.user_data = {
            'username': 'testuser_api',
            'email': 'testuser_api@example.com',
            'password': 'password123',
            'password2': 'password123'
        }
        self.user_login_data = {
            'email': 'testuser_api@example.com', # CustomLoginSerializer uses email
            'password': 'password123'
        }

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='testuser_api').exists())
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_login(self):
        # First, register the user
        self.client.post(self.register_url, self.user_data, format='json')
        # Then, log in
        response = self.client.post(self.login_url, self.user_login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], self.user_data['username'])

    def test_user_logout(self):
        self.client.post(self.register_url, self.user_data, format='json')
        login_response = self.client.post(self.login_url, self.user_login_data, format='json')
        access_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        logout_response = self.client.post(self.logout_url, {}, format='json') # Logout might need refresh token depending on setup
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK) # Or 204 if no content

    def test_get_user_details_authenticated(self):
        self.client.post(self.register_url, self.user_data, format='json')
        login_response = self.client.post(self.login_url, self.user_login_data, format='json')
        access_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.get(self.user_details_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user_data['username'])

    def test_get_user_details_unauthenticated(self):
        response = self.client.get(self.user_details_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_verify(self):
        self.client.post(self.register_url, self.user_data, format='json')
        login_response = self.client.post(self.login_url, self.user_login_data, format='json')
        access_token = login_response.data['access']
        
        response = self.client.post(self.token_verify_url, {'token': access_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_refresh(self):
        self.client.post(self.register_url, self.user_data, format='json')
        login_response = self.client.post(self.login_url, self.user_login_data, format='json')
        refresh_token = login_response.data['refresh']
        
        response = self.client.post(self.token_refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


class ProfileAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='user1_profile_api', email='user1_profile@api.com', password='password1')
        self.user2 = User.objects.create_user(username='user2_profile_api', email='user2_profile@api.com', password='password2')

        # Profiles are created via signals or need to be created manually if signals are not used for tests
        self.profile1, _ = Profile.objects.get_or_create(user=self.user1, defaults={'bio': 'User 1 Bio API'})
        self.profile2, _ = Profile.objects.get_or_create(user=self.user2, defaults={'bio': 'User 2 Bio API'})

        self.profile_list_create_url = reverse('profile-list') # Corresponds to router.register('profile', ...)
        self.my_profile_url = reverse('my-profile')
        self.profile_detail_url = lambda pk: reverse('profile-detail', kwargs={'pk': pk})
        self.profile_upload_pic_url = reverse('profile-picture-upload')

        # Authenticate user1 for most tests
        self.client.login(username='user1_profile_api', password='password1')

    def test_get_my_profile(self):
        response = self.client.get(self.my_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], self.user1.username)
        self.assertEqual(response.data['bio'], self.profile1.bio)

    def test_update_my_profile(self):
        updated_data = {'bio': 'Updated bio for user1', 'profile_type': 'AUTHOR'}
        response = self.client.patch(self.my_profile_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile1.refresh_from_db()
        self.assertEqual(self.profile1.bio, 'Updated bio for user1')
        self.assertEqual(self.profile1.profile_type, 'AUTHOR')

    def test_list_profiles_authenticated(self):
        response = self.client.get(self.profile_list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assuming pagination, check if results exist
        self.assertGreaterEqual(len(response.data.get('results', response.data)), 2) # user1 and user2 profiles

    def test_retrieve_profile_authenticated(self):
        response = self.client.get(self.profile_detail_url(self.profile2.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], self.user2.username)

    def test_cannot_update_other_user_profile(self):
        # user1 tries to update user2's profile
        updated_data = {'bio': 'Attempted update by another user'}
        response = self.client.patch(self.profile_detail_url(self.profile2.pk), updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # IsOwnerOrReadOnly permission

    def test_create_profile_fails_if_already_exists(self):
        # User1 already has a profile, attempt to create another one should fail
        # The ProfileViewSet's create method explicitly checks for this
        profile_data = {'bio': 'Trying to create another profile', 'profile_type': 'REGULAR'}
        # Note: The default 'profile-list' POST action is for creating. 
        # The view's create method handles user assignment.
        response = self.client.post(self.profile_list_create_url, profile_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'User already has a profile')

    def test_upload_profile_picture(self):
        # Create a dummy image file
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'file_content',
            content_type='image/jpeg'
        )
        response = self.client.post(self.profile_upload_pic_url, {'profile_pic': image}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profile_pic_url', response.data)
        self.profile1.refresh_from_db()
        self.assertTrue(self.profile1.profile_pic.url.startswith('http')) # Check if URL is set

    def test_upload_profile_picture_no_file(self):
        response = self.client.post(self.profile_upload_pic_url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'No image provided')

    def test_upload_profile_picture_invalid_file_type(self):
        text_file = SimpleUploadedFile(
            name='test_file.txt',
            content=b'some text',
            content_type='text/plain'
        )
        response = self.client.post(self.profile_upload_pic_url, {'profile_pic': text_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid file type')

    def test_get_profile_by_username_query_param(self):
        # user1 is authenticated
        response = self.client.get(self.profile_list_create_url, {'username': self.user2.username})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data) # Handle paginated or non-paginated response
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['user']['username'], self.user2.username)

    def test_unauthenticated_access_to_profile_endpoints(self):
        self.client.logout() # Ensure client is unauthenticated
        
        response_my_profile = self.client.get(self.my_profile_url)
        self.assertEqual(response_my_profile.status_code, status.HTTP_401_UNAUTHORIZED)

        response_list = self.client.get(self.profile_list_create_url)
        self.assertEqual(response_list.status_code, status.HTTP_401_UNAUTHORIZED)

        response_detail = self.client.get(self.profile_detail_url(self.profile1.pk))
        self.assertEqual(response_detail.status_code, status.HTTP_401_UNAUTHORIZED)

        response_upload = self.client.post(self.profile_upload_pic_url, {}, format='multipart')
        self.assertEqual(response_upload.status_code, status.HTTP_401_UNAUTHORIZED)