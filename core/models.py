from django.db import models
import re

# Create your models here.
class EmailAddress(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_generic = models.BooleanField(default=False, help_text="Whether this is a generic email (e.g. no-reply@company.com)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email

class Contact(models.Model):
    name = models.CharField(max_length=255)
    emails = models.ManyToManyField(EmailAddress, related_name='contacts')
    knowledge = models.TextField(blank=True, null=True, help_text="Context for AI to understand this contact")

    @property
    def primary_email(self):
        return self.emails.first()

    def __str__(self):
        if self.name and self.primary_email:
            return f"{self.name} <{self.primary_email}>"
        return self.name or self.primary_email

class Label(models.Model):
    name = models.CharField(max_length=100)
    gmail_label_id = models.CharField(max_length=100, unique=True)
    label_knowledge = models.TextField(blank=True, null=True, help_text="Context for AI to understand this label")

    def __str__(self):
        return self.name

class Email(models.Model):
    gmail_message_id = models.CharField(max_length=255, unique=True)
    gmail_thread_id = models.CharField(max_length=255)
    date = models.DateTimeField()
    sender_str = models.CharField(max_length=255)
    sender = models.ForeignKey(Contact, on_delete=models.PROTECT, related_name="sent_emails")
    to_contacts = models.ManyToManyField(Contact, related_name="to_emails")
    cc_contacts = models.ManyToManyField(Contact, related_name="cc_emails", blank=True)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    snippet = models.TextField()
    labels = models.ManyToManyField(Label, blank=True)
    thread = models.ForeignKey("Thread", on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def truncated_body(self):
        """ This property returns the body of the email without the quoted text from previous emails."""
        truncated_body = re.sub(r"On.*wrote:", "", self.body, count=1)
        return truncated_body

    def __str__(self):
        return f"{self.subject} - {self.date} - from {self.sender}"

class Thread(models.Model):
    gmail_thread_id = models.CharField(max_length=255)
    labels = models.ManyToManyField(Label, blank=True)
    last_email = models.ForeignKey(Email, on_delete=models.SET_NULL, null=True, blank=True, related_name="last_email")

    #subject and date are readonly fields. They are set when the first email is added to the thread
    # and are equal to the date and subject of the first email

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
        participants = set()
        for email in self.email_set.all(): # type: ignore[attr-defined]
            participants.add(email.sender)
            for receiver in email.to.all():
                participants.add(receiver)
            for cc in email.cc.all():
                participants.add(cc)
        return list(participants)

    @property
    def number_of_emails(self):
        return self.email_set.count() # type: ignore[attr-defined]

    def __str__(self):
        if self.email_set.exists(): # type: ignore[attr-defined]
            return f"Thread {self.email_set.first().subject} - {self.email_set.first().date}" # type: ignore[attr-defined]
        return f"Thread {self.id}" # type: ignore[attr-defined]


class ThreadSummary(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    summary = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Summary for Thread {self.thread.id} at {self.timestamp}"

class Action(models.Model):
    ACTION_CHOICES = [
        ("none", "None"),
        ("info", "Information"),
        ("respond", "To Respond"),
        ("follow", "To Follow"),
    ]

    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    email = models.OneToOneField(Email, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    draft_response = models.TextField(blank=True, null=True)
    rationale = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Action for Email {self.email_id}: {self.get_action_display()}"

class SpecificInstruction(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True)
    label = models.ForeignKey(Label, on_delete=models.SET_NULL, null=True, blank=True)
    instruction = models.TextField()

    def __str__(self):
        parts = []
        if self.contact:
            parts.append(f"Contact: {self.contact.name}")
        if self.label:
            parts.append(f"Tag: {self.label.name}")
        return " | ".join(parts) or "Global Instruction"

class SystemParameter(models.Model):
    key = models.CharField(max_length=50, unique=True)
    value = models.TextField()

    def __str__(self):
        return f"{self.key}: {self.value}"
