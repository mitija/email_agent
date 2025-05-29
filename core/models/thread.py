from django.db import models
from .label import Label
from .base import TimestampedModel

class Thread(TimestampedModel):
    gmail_thread_id = models.CharField(max_length=255)
    labels = models.ManyToManyField(Label, blank=True)
    last_email = models.ForeignKey('Email', on_delete=models.SET_NULL, null=True, blank=True, related_name="last_email")

    @property
    def subject(self):
        if self.email_set.exists(): # type: ignore[attr-defined]
            return self.email_set.first().subject # type: ignore[attr-defined]
        return ""

    @property
    def date(self):
        if self.email_set.exists(): # type: ignore[attr-defined]
            return self.email_set.first().date # type: ignore[attr-defined]
        return None

    @property
    def participants(self):
        """Returns a list of unique Contact objects that participated in this thread"""
        participants_str = set()
        for email in self.email_set.all(): # type: ignore[attr-defined]
            participants_str.add(email.sender_str)
            for receiver in email.to_str.all():
                participants_str.add(receiver)
            for cc in email.cc_str.all():
                participants_str.add(cc)
        return list(participants_str)

    @property
    def number_of_emails(self):
        return self.email_set.count()

    @property
    def initiated_by(self):
        first_email = self.first_email
        return "xxxx"

    @property
    def first_email(self):
        return self.email_set.first()

    def __str__(self):
        if self.email_set.exists(): # type: ignore[attr-defined]
            return f"Thread {self.email_set.first().subject} - {self.email_set.first().date}" # type: ignore[attr-defined]
        return f"Thread {self.id}" # type: ignore[attr-defined] 