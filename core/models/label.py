from django.db import models
from .base import TimestampedModel

class Label(TimestampedModel):
    name = models.CharField(max_length=100)
    gmail_label_id = models.CharField(max_length=100, unique=True)
    label_knowledge = models.TextField(blank=True, null=True, help_text="Context for AI to understand this label")

    def __str__(self):
        return self.name 