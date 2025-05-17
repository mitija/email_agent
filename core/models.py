from django.db import models
import re
import unicodedata

# Create your models here.
class EmailAddress(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_generic = models.BooleanField(default=False, help_text="Whether this is a generic email (e.g. no-reply@company.com)")

    def __str__(self):
        return self.email

def _extract_email_and_name(original_string):
    """ This method will extract the email and name from the email string
    parameters: email - a string with the format "Name <email>"
    It will return a tuple with the name and email
    """
    name = ""
    email = ""

    if "<" in original_string:
        name = original_string.split("<")[0].strip()
        email = original_string.split("<")[1].split(">")[0].strip()
    else:
        email = original_string.strip()

    if not name:
        name = email.strip()

    if "@" in name:
        name = name.split("@")[0]

    # We try to normalize the name
    name = re.sub(r'-', ' ', name)
    name = re.sub(r'\.', ' ', name)
    name = re.sub(r'_', ' ', name)

    # We remove " from name
    name = re.sub(r'"', '', name)
    name = name.strip()

    # remove any non-ascii characters and replace them by their ascii equivalent
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')

    # remove double spaces in name
    name = re.sub(r'\s+', ' ', name)
    # Capitalize each word in name
    name = name.title()

    return (name, email)

class Contact(models.Model):
    name = models.CharField(max_length=255)
    emails = models.ManyToManyField(EmailAddress, related_name='contacts')
    knowledge = models.TextField(blank=True, null=True, help_text="Context for AI to understand this contact")

    @property
    def primary_email(self):
        return self.emails.first()

    def __str__(self):
        if self.name and self.primary_email:
            return f"{self.name} <{self.primary_email.email}>"
        return self.name or self.primary_email.email

class EmailString(models.Model):
    original_string = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    email = models.ForeignKey(EmailAddress, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True)

    # On save, we update the name and email
    def save(self, *args, **kwargs):
        name, email = _extract_email_and_name(self.original_string)
        self.name = name
        self.email = EmailAddress.objects.get_or_create(email=email)[0]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.original_string


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
    sender_str = models.ForeignKey(EmailString, on_delete=models.PROTECT, related_name="sent_emails")
    to_str = models.ManyToManyField(EmailString, related_name="to_emails")
    cc_str = models.ManyToManyField(EmailString, related_name="cc_emails")
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
        return f"{self.subject} - {self.date} - from {self.sender_str}"

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
        """Returns a list of unique Contact objects that participated in this thread"""
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
        return self.email_set.count()

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

class SystemParameter(models.Model):
    key = models.CharField(max_length=50, unique=True)
    value = models.TextField()

    def __str__(self):
        return f"{self.key}: {self.value}"
