from django.db import models
from .email_address import EmailAddress
from .base import TimestampedModel

class Contact(TimestampedModel):
    name = models.CharField(max_length=255)
    emails = models.ManyToManyField(EmailAddress, related_name='contacts')
    knowledge = models.TextField(blank=True, null=True, help_text="Context for AI to understand this contact")

    @property
    def primary_email(self):
        return self.emails.first()

    def __str__(self):
        return f"{self.name} - {self.id}" 