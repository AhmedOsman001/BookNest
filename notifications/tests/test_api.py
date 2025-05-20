from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from notifications.models import Notification, NotificationType
from users.models import User  # Assuming User model from your project structure
from django.contrib.contenttypes.models import ContentType

class NotificationAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='testuser1', password='password123', email='test1@example.com')
        self.user2 = User.objects.create_user(username='testuser2', password='password456', email='test2@example.com')

        self.type1 = NotificationType.objects.create(name='Test Notification Type 1', description='Desc 1')
        self.type2 = NotificationType.objects.create(name='Test Notification Type 2', description='Desc 2')

        # Actor content type (e.g., another user)
        self.actor_content_type = ContentType.objects.get_for_model(self.user2)

        self.notification1 = Notification.objects.create(
            recipient=self.user1,
            actor_content_type=self.actor_content_type,
            actor_object_id=self.user2.pk,
            verb='sent you a message',
            notification_type=self.type1
        )
        self.notification2 = Notification.objects.create(
            recipient=self.user1,
            verb='liked your post',
            notification_type=self.type2,
            read=True
        )
        self.notification3 = Notification.objects.create(
            recipient=self.user2, # Different recipient
            verb='commented on your photo',
            notification_type=self.type1
        )

        self.list_create_url = reverse('notification-list') # GET for list, POST for create (though create might be separate)
        self.detail_url = lambda id: reverse('notification-detail', kwargs={'id': id})
        self.mark_read_url = lambda id: reverse('notification-mark-read', kwargs={'id': id})
        self.mark_unread_url = lambda id: reverse('notification-mark-unread', kwargs={'id': id})
        self.mark_all_read_url = reverse('notification-mark-all-read')
        self.unread_count_url = reverse('notification-unread-count')
        self.type_list_url = reverse('notification-type-list')
        self.type_detail_url = lambda id: reverse('notification-type-detail', kwargs={'id': id})
        # Assuming create, update, delete for notifications might be restricted or handled by signals
        # For now, focusing on read operations and marking status

    def test_get_notification_list_unauthenticated(self):
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) # Or 403 depending on setup

    def test_get_notification_list_authenticated(self):
        self.client.login(username='testuser1', password='password123')
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return notifications for user1 (notification1, notification2)
        self.assertEqual(len(response.data['results']), 2) 
        self.assertEqual(response.data['results'][0]['verb'], self.notification2.verb) # Ordered by -timestamp
        self.assertEqual(response.data['results'][1]['verb'], self.notification1.verb)

    def test_get_notification_detail_authenticated(self):
        self.client.login(username='testuser1', password='password123')
        response = self.client.get(self.detail_url(self.notification1.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['verb'], self.notification1.verb)

    def test_get_notification_detail_unauthorized_access(self):
        # user2 trying to access user1's notification
        self.client.login(username='testuser2', password='password456')
        response = self.client.get(self.detail_url(self.notification1.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Or 403

    def test_mark_notification_as_read(self):
        self.client.login(username='testuser1', password='password123')
        self.assertFalse(Notification.objects.get(id=self.notification1.id).read)
        response = self.client.post(self.mark_read_url(self.notification1.id)) # Assuming POST or PATCH
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.read)

    def test_mark_notification_as_unread(self):
        self.client.login(username='testuser1', password='password123')
        self.assertTrue(Notification.objects.get(id=self.notification2.id).read)
        response = self.client.post(self.mark_unread_url(self.notification2.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification2.refresh_from_db()
        self.assertFalse(self.notification2.read)

    def test_mark_all_notifications_as_read(self):
        self.client.login(username='testuser1', password='password123')
        # user1 has one unread notification (notification1)
        self.assertEqual(Notification.objects.filter(recipient=self.user1, read=False).count(), 1)
        response = self.client.post(self.mark_all_read_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Or 204
        self.assertEqual(Notification.objects.filter(recipient=self.user1, read=False).count(), 0)

    def test_get_unread_notification_count(self):
        self.client.login(username='testuser1', password='password123')
        # user1 has one unread notification (notification1) initially in this test setup
        Notification.objects.filter(id=self.notification1.id).update(read=False)
        Notification.objects.filter(id=self.notification2.id).update(read=True)
        response = self.client.get(self.unread_count_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 1)

        # Mark it as read and check again
        self.notification1.mark_as_read()
        response = self.client.get(self.unread_count_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 0)

    def test_get_notification_type_list(self):
        # Notification types are usually public
        response = self.client.get(self.type_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), NotificationType.objects.count())

    def test_get_notification_type_detail(self):
        response = self.client.get(self.type_detail_url(self.type1.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.type1.name)

    # Placeholder for create notification if it's a direct API endpoint
    # def test_create_notification_authenticated(self):
    #     self.client.login(username='testuser1', password='password123')
    #     actor_ct = ContentType.objects.get_for_model(self.user2)
    #     data = {
    #         'recipient': self.user1.pk,
    #         'actor_content_type': actor_ct.pk,
    #         'actor_object_id': self.user2.pk,
    #         'verb': 'tested creation',
    #         'notification_type': self.type1.pk
    #     }
    #     create_url = reverse('notification-create') # Assuming this URL exists
    #     response = self.client.post(create_url, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     self.assertEqual(Notification.objects.filter(recipient=self.user1, verb='tested creation').count(), 1)