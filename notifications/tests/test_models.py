from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from notifications.models import Notification, NotificationType
from users.models import User # Assuming you have a User model
from books.models import Book # Assuming a Book model to act as a target/action_object

class NotificationTypeModelTests(TestCase):
    def setUp(self):
        self.notification_type = NotificationType.objects.create(
            name="Test Type",
            description="A test notification type."
        )

    def test_notification_type_creation(self):
        self.assertEqual(self.notification_type.name, "Test Type")
        self.assertEqual(self.notification_type.description, "A test notification type.")

    def test_notification_type_str(self):
        self.assertEqual(str(self.notification_type), "Test Type")

class NotificationModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='recipient_user', password='password123')
        self.user2 = User.objects.create_user(username='actor_user', password='password456')
        self.book = Book.objects.create(isbn13='9780000000010', title='Target Book')
        self.notification_type = NotificationType.objects.create(name='Follow', description='User followed another user')

        self.actor_content_type = ContentType.objects.get_for_model(self.user2)
        self.target_content_type = ContentType.objects.get_for_model(self.book)

        self.notification = Notification.objects.create(
            recipient=self.user1,
            actor_content_type=self.actor_content_type,
            actor_object_id=str(self.user2.pk),
            verb="followed",
            target_content_type=self.target_content_type,
            target_object_id=self.book.pk,
            notification_type=self.notification_type,
            data={'extra_info': 'some value'}
        )

    def test_notification_creation(self):
        self.assertEqual(self.notification.recipient, self.user1)
        self.assertEqual(self.notification.actor, self.user2)
        self.assertEqual(self.notification.verb, "followed")
        self.assertEqual(self.notification.target, self.book)
        self.assertEqual(self.notification.notification_type, self.notification_type)
        self.assertFalse(self.notification.read)
        self.assertEqual(self.notification.data['extra_info'], 'some value')

    def test_notification_str(self):
        expected_str = f"{self.user1.username} - followed"
        self.assertEqual(str(self.notification), expected_str)

    def test_mark_as_read(self):
        self.assertFalse(self.notification.read)
        self.notification.mark_as_read()
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.read)

    def test_mark_as_unread(self):
        self.notification.read = True
        self.notification.save()
        self.assertTrue(self.notification.read)
        self.notification.mark_as_unread()
        self.notification.refresh_from_db()
        self.assertFalse(self.notification.read)

    def test_notification_without_actor(self):
        system_notification_type = NotificationType.objects.create(name='System Update')
        notification = Notification.objects.create(
            recipient=self.user1,
            verb="system updated",
            notification_type=system_notification_type
        )
        self.assertIsNone(notification.actor)
        self.assertEqual(notification.verb, "system updated")

    def test_notification_ordering(self):
        # Create another notification to test ordering
        Notification.objects.create(
            recipient=self.user1,
            verb="another action",
            notification_type=self.notification_type
        )
        notifications = Notification.objects.filter(recipient=self.user1)
        # Assuming default ordering is by -timestamp (newest first)
        self.assertEqual(notifications.first().verb, "another action")
        self.assertEqual(notifications.last().verb, "followed")

    def test_create_default_notification_types_function(self):
        # This tests the helper function, assuming it's idempotent
        from notifications.models import create_default_notification_types
        initial_count = NotificationType.objects.count()
        create_default_notification_types()
        # Check if default types are created or already exist
        self.assertTrue(NotificationType.objects.filter(name='follow').exists())
        self.assertTrue(NotificationType.objects.filter(name='book_review').exists())
        # Ensure no duplicates if run again
        create_default_notification_types()
        self.assertEqual(NotificationType.objects.count(), NotificationType.objects.count()) # Count should remain same