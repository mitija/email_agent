from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from core.models.thread import Thread
from core.models.email import Email
from core.models.email_string import EmailString
from django.contrib.auth.models import User

class TimeframeThreadsViewTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

        # Create email strings using original_string
        self.sender = EmailString.objects.create(original_string="test@example.com")
        self.recipient = EmailString.objects.create(original_string="recipient@example.com")

        # Create test threads
        self.thread1 = Thread.objects.create(
            gmail_thread_id="test_thread_1"
        )
        self.thread2 = Thread.objects.create(
            gmail_thread_id="test_thread_2"
        )

        # Create emails with different dates
        now = timezone.now()
        
        # Email from 30 minutes ago
        self.email1 = Email.objects.create(
            thread=self.thread1,
            thread_id=self.thread1.id,
            subject="Test Thread 1",
            date=now - timedelta(minutes=30),
            snippet="Test snippet 1",
            gmail_message_id="test_message_1",
            gmail_thread_id="test_thread_1",
            sender_str=self.sender,
            body="Test body 1"
        )
        self.email1.to_str.add(self.recipient)

        # Email from 10 hours ago
        self.email2 = Email.objects.create(
            thread=self.thread2,
            thread_id=self.thread2.id,
            subject="Test Thread 2",
            date=now - timedelta(hours=10),
            snippet="Test snippet 2",
            gmail_message_id="test_message_2",
            gmail_thread_id="test_thread_2",
            sender_str=self.sender,
            body="Test body 2"
        )
        self.email2.to_str.add(self.recipient)

        # Update thread summaries
        self.thread1.last_email = self.email1
        self.thread1.save()
        self.thread2.last_email = self.email2
        self.thread2.save()

    def test_timeframe_1h(self):
        """Test that only threads with emails from the last hour are shown"""
        response = self.client.get(reverse('timeframe_threads') + '?timeframe=1h')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/timeframe_threads.html')
        
        # Should only show thread1 (30 minutes ago)
        self.assertContains(response, "Test Thread 1")
        self.assertNotContains(response, "Test Thread 2")

    def test_timeframe_8h(self):
        """Test that threads with emails from the last 8 hours are shown"""
        response = self.client.get(reverse('timeframe_threads') + '?timeframe=8h')
        self.assertEqual(response.status_code, 200)
        
        # Should only show thread1 (30 minutes ago)
        self.assertContains(response, "Test Thread 1")
        self.assertNotContains(response, "Test Thread 2")

    def test_timeframe_12h(self):
        """Test that threads with emails from the last 12 hours are shown"""
        response = self.client.get(reverse('timeframe_threads') + '?timeframe=12h')
        self.assertEqual(response.status_code, 200)
        
        # Should show both threads
        self.assertContains(response, "Test Thread 1")
        self.assertContains(response, "Test Thread 2")

    def test_timeframe_24h(self):
        """Test that threads with emails from the last 24 hours are shown"""
        response = self.client.get(reverse('timeframe_threads') + '?timeframe=24h')
        self.assertEqual(response.status_code, 200)
        
        # Should show both threads
        self.assertContains(response, "Test Thread 1")
        self.assertContains(response, "Test Thread 2")

    def test_default_timeframe(self):
        """Test that default timeframe (24h) is used when no timeframe is specified"""
        response = self.client.get(reverse('timeframe_threads'))
        self.assertEqual(response.status_code, 200)
        
        # Should show both threads
        self.assertContains(response, "Test Thread 1")
        self.assertContains(response, "Test Thread 2")

    def test_authentication_required(self):
        """Test that authentication is required to access the view"""
        self.client.logout()
        response = self.client.get(reverse('timeframe_threads'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login page 