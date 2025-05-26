import re
from django.db import models
from .email_string import EmailString
from .label import Label
from .base import TimestampedModel

class Email(TimestampedModel):
    gmail_message_id = models.CharField(max_length=255, unique=True)
    gmail_thread_id = models.CharField(max_length=255)
    date = models.DateTimeField()
    sender_str = models.ForeignKey(EmailString, on_delete=models.PROTECT, related_name="sent_emails")
    to_str = models.ManyToManyField(EmailString, related_name="to_emails")
    cc_str = models.ManyToManyField(EmailString, related_name="cc_emails")
    subject = models.CharField(max_length=255)
    body = models.TextField()
    snippet = models.TextField()
    labels = models.ManyToManyField(Label, blank=True)
    thread = models.ForeignKey('Thread', on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def truncated_body(self):
        """ This property returns the body of the email without the quoted text from previous emails.
        Handles various email client quote patterns including:
        - "On ... wrote:" (Gmail)
        - "From: ... Sent: ... To: ... Subject: ..." (Outlook)
        - "> " (common quote marker)
        - "-----Original Message-----" (Outlook)
        """
        # First, try to find the last occurrence of common quote markers
        patterns = [
            r"On.*wrote:",  # Gmail style
            r"From:.*\nSent:.*\nTo:.*\nSubject:",  # Outlook style
            r"-----Original Message-----",  # Outlook style
            r"^>.*$",  # Common quote marker
        ]
        
        # Find the earliest occurrence of any quote pattern
        earliest_quote = len(self.body)
        for pattern in patterns:
            matches = list(re.finditer(pattern, self.body, re.MULTILINE))
            if matches:
                earliest_quote = min(earliest_quote, matches[0].start())
        
        # Return only the content before the first quote
        return self.body[:earliest_quote].strip()

    def __str__(self):
        return f"{self.subject} - {self.date} - from {self.sender_str}" 