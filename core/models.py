from django.db import models

# Create your models here.
class Contact(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.name or self.email

class Tag(models.Model):
    name = models.CharField(max_length=100)
    rule = models.TextField(help_text="Instructions for AI to assign this tag")

    def __str__(self):
        return self.name

class Email(models.Model):
    gmail_message_id = models.CharField(max_length=255, unique=True)
    gmail_thread_id = models.CharField(max_length=255)
    date = models.DateTimeField()
    sender = models.ManyToManyField(Contact, related_name="sent_emails")
    receiver = models.ManyToManyField(Contact, related_name="received_emails")
    subject = models.CharField(max_length=255)
    content = models.TextField()

    def __str__(self):
        return f"{self.subject} - {self.date}"

class Thread(models.Model):
    gmail_thread_id = models.CharField(max_length=255)
    emails = models.ManyToManyField(Email)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return f"Thread {self.id}"

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
    tag = models.ForeignKey(Tag, on_delete=models.SET_NULL, null=True, blank=True)
    instruction = models.TextField()

    def __str__(self):
        parts = []
        if self.contact:
            parts.append(f"Contact: {self.contact.name}")
        if self.tag:
            parts.append(f"Tag: {self.tag.name}")
        return " | ".join(parts) or "Global Instruction"

class SystemParameter(models.Model):
    key = models.CharField(max_length=50, unique=True)
    value = models.TextField()

    def __str__(self):
        return f"{self.key}: {self.value}"
