import re
from django.db import models
from .email_string import EmailString
from .label import Label
from .base import TimestampedModel
from .utils import remove_quoted_text

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
        """Returns the body of the email without the quoted text from previous emails."""
        return remove_quoted_text(self.body)

    def __str__(self):
        return f"{self.subject} - {self.date} - from {self.sender_str}" 