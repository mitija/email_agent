from django.db import models
from .thread import Thread
from .email import Email
from .base import TimestampedModel
import json

class ThreadSummary(TimestampedModel):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    summary = models.TextField()
    action = models.CharField(max_length=20, null=True, blank=True, choices=[
        ('IGNORE', 'Ignore'),
        ('NEED_TO_KNOW', 'Need to Know'),
        ('NEED_TO_RESPOND', 'Need to Respond')
    ])
    rationale = models.TextField()
    participants = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    @property
    def formatted_participants(self):
        if self.participants:
            return json.dumps(self.participants, indent=2)
        return ""

    def __str__(self):
        return f"Summary for Thread {self.thread.id} at {self.timestamp}" 