from django.db import models
from .thread import Thread
from .email import Email
from .base import TimestampedModel

class ThreadSummary(TimestampedModel):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    summary = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Summary for Thread {self.thread.id} at {self.timestamp}" 