from django.db import models
from .email_address import EmailAddress
from .base import TimestampedModel

class ContactManager(models.Manager):
    def search_similar_names(self, name, email=None):
        from core.utils import search_similar_contacts
        result = search_similar_contacts(name, email)
        if result is None:
            return []
        if isinstance(result, list):
            return result
        return [result]

class Contact(TimestampedModel):
    name = models.CharField(max_length=255)
    emails = models.ManyToManyField(EmailAddress, related_name='contacts')
    knowledge = models.TextField(blank=True, null=True, help_text="Context for AI to understand this contact")

    objects = ContactManager()

    @property
    def primary_email(self):
        return self.emails.first()

    def __str__(self):
        return f"{self.name} - {self.id}" 