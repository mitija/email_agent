from django.db import models
from .base import TimestampedModel

class SystemParameter(TimestampedModel):
    key = models.CharField(max_length=50, unique=True)
    value = models.TextField()

    def __str__(self):
        return f"{self.key}: {self.value}" 