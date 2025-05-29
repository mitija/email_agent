from django.test import TestCase
from core.utils import is_calendar_invite
from core.models import Email, EmailString, EmailAddress, Thread
from datetime import datetime
from django.utils import timezone

class CalendarInviteDetectionTest(TestCase):
    def setUp(self):
        # Create common test objects
        self.email_address = EmailAddress.objects.create(email="test@example.com")
        self.sender_str = EmailString.objects.create(
            original_string="Test Sender <test@example.com>",
            name="Test Sender",
            email=self.email_address
        )
        self.thread = Thread.objects.create(gmail_thread_id="test_thread_id")

    def test_subject_based_detection(self):
        test_cases = [
            {
                'name': 'Declined with colon',
                'message': {
                    'Subject': 'Declined: SME committee',
                    'Body': '',
                    'payload': {'headers': []}
                },
                'expected': True
            },
            {
                'name': 'Declined without colon',
                'message': {
                    'Subject': 'Declined SME committee',
                    'Body': '',
                    'payload': {'headers': []}
                },
                'expected': True
            },
            {
                'name': 'Accepted with colon',
                'message': {
                    'Subject': 'Accepted: Team Meeting',
                    'Body': '',
                    'payload': {'headers': []}
                },
                'expected': True
            },
            {
                'name': 'Tentative with colon',
                'message': {
                    'Subject': 'Tentative: Project Review',
                    'Body': '',
                    'payload': {'headers': []}
                },
                'expected': True
            },
            {
                'name': 'Regular email',
                'message': {
                    'Subject': 'Regular email subject',
                    'Body': '',
                    'payload': {'headers': []}
                },
                'expected': False
            }
        ]

        for test_case in test_cases:
            with self.subTest(test_case['name']):
                result = is_calendar_invite(
                    subject=test_case['message']['Subject'],
                    body=test_case['message']['Body'],
                    headers=test_case['message']['payload']['headers']
                )
                self.assertEqual(
                    result, 
                    test_case['expected'],
                    f"Test case '{test_case['name']}' failed. Expected {test_case['expected']}, got {result}"
                )

    def test_body_based_detection(self):
        test_cases = [
            {
                'name': 'Calendar invitation in body',
                'message': {
                    'Subject': 'Regular subject',
                    'Body': 'This is a calendar invitation for a meeting',
                    'payload': {'headers': []}
                },
                'expected': True
            },
            {
                'name': 'Meeting request in body',
                'message': {
                    'Subject': 'Regular subject',
                    'Body': 'You have been invited to a meeting',
                    'payload': {'headers': []}
                },
                'expected': True
            },
            {
                'name': 'Regular email body',
                'message': {
                    'Subject': 'Regular subject',
                    'Body': 'This is a regular email body',
                    'payload': {'headers': []}
                },
                'expected': False
            }
        ]

        for test_case in test_cases:
            with self.subTest(test_case['name']):
                result = is_calendar_invite(
                    subject=test_case['message']['Subject'],
                    body=test_case['message']['Body'],
                    headers=test_case['message']['payload']['headers']
                )
                self.assertEqual(
                    result, 
                    test_case['expected'],
                    f"Test case '{test_case['name']}' failed. Expected {test_case['expected']}, got {result}"
                )

    def test_header_based_detection(self):
        test_cases = [
            {
                'name': 'Microsoft calendar header',
                'message': {
                    'Subject': 'Regular subject',
                    'Body': '',
                    'payload': {
                        'headers': [
                            {'name': 'x-microsoft-cdo-busystatus', 'value': 'busy'}
                        ]
                    }
                },
                'expected': True
            },
            {
                'name': 'Content class header',
                'message': {
                    'Subject': 'Regular subject',
                    'Body': '',
                    'payload': {
                        'headers': [
                            {'name': 'content-class', 'value': 'urn:content-classes:calendarmessage'}
                        ]
                    }
                },
                'expected': True
            },
            {
                'name': 'Regular headers',
                'message': {
                    'Subject': 'Regular subject',
                    'Body': '',
                    'payload': {
                        'headers': [
                            {'name': 'From', 'value': 'test@example.com'}
                        ]
                    }
                },
                'expected': False
            }
        ]

        for test_case in test_cases:
            with self.subTest(test_case['name']):
                result = is_calendar_invite(
                    subject=test_case['message']['Subject'],
                    body=test_case['message']['Body'],
                    headers=test_case['message']['payload']['headers']
                )
                self.assertEqual(
                    result, 
                    test_case['expected'],
                    f"Test case '{test_case['name']}' failed. Expected {test_case['expected']}, got {result}"
                )

    def test_email_model_detection(self):
        test_cases = [
            {
                'name': 'Declined with colon',
                'subject': 'Declined: SME committee',
                'body': '',
                'expected': True
            },
            {
                'name': 'Declined without colon',
                'subject': 'Declined SME committee',
                'body': '',
                'expected': True
            },
            {
                'name': 'Accepted with colon',
                'subject': 'Accepted: Team Meeting',
                'body': '',
                'expected': True
            },
            {
                'name': 'Tentative with colon',
                'subject': 'Tentative: Project Review',
                'body': '',
                'expected': True
            },
            {
                'name': 'Calendar invitation in body',
                'subject': 'Regular subject',
                'body': 'This is a calendar invitation for a meeting',
                'expected': True
            },
            {
                'name': 'Meeting request in body',
                'subject': 'Regular subject',
                'body': 'You have been invited to a meeting',
                'expected': True
            },
            {
                'name': 'Regular email',
                'subject': 'Regular email subject',
                'body': 'This is a regular email body',
                'expected': False
            }
        ]

        for test_case in test_cases:
            with self.subTest(test_case['name']):
                # Create an Email object for testing
                email = Email.objects.create(
                    gmail_message_id=f"test_message_{test_case['name']}",
                    gmail_thread_id=self.thread.gmail_thread_id,
                    date=timezone.now(),
                    subject=test_case['subject'],
                    body=test_case['body'],
                    snippet=test_case['body'][:100] if test_case['body'] else '',
                    sender_str=self.sender_str,
                    thread=self.thread
                )

                # Create headers list from the Email object
                headers = [
                    {'name': 'From', 'value': email.sender_str.original_string},
                    {'name': 'Subject', 'value': email.subject},
                    {'name': 'To', 'value': ', '.join(to.original_string for to in email.to_str.all())},
                    {'name': 'Cc', 'value': ', '.join(cc.original_string for cc in email.cc_str.all())},
                ]

                # Test calendar detection
                result = is_calendar_invite(
                    subject=email.subject,
                    body=email.body,
                    headers=headers
                )
                self.assertEqual(
                    result, 
                    test_case['expected'],
                    f"Test case '{test_case['name']}' failed. Expected {test_case['expected']}, got {result}"
                ) 