from django.db import models
from .email_address import EmailAddress
from .contact import Contact
from core.utils import extract_email_and_name, search_similar_contacts
from .base import TimestampedModel

class EmailString(TimestampedModel):
    original_string = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    email = models.ForeignKey(EmailAddress, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True)
    reviewed = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        name, email = extract_email_and_name(self.original_string)
        self.name = name
        self.email = EmailAddress.objects.get_or_create(email=email)[0]

        if not self.contact:
            contact = search_similar_contacts(name, email)
            if contact:
                self.contact = contact
                # We need to add the email to the contact if it is not already there
                if self.email not in self.contact.emails.all():
                    self.contact.emails.add(self.email) 
                    self.contact.save()
            else:
                self.contact = Contact.objects.create(name=name)
                self.contact.emails.add(self.email)
                self.contact.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.original_string 