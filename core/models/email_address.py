from django.db import models
from .base import TimestampedModel

class EmailAddress(TimestampedModel):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_generic = models.BooleanField(default=False, help_text="Whether this is a generic email (e.g. no-reply@company.com)")

    def __str__(self):
        return self.email 