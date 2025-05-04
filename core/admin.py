from django.contrib import admin
from .models import Contact, Email, Tag, Thread, ThreadSummary, Action, SpecificInstruction, SystemParameter
from .gmail_helper import gmail_helper
from datetime import datetime, timedelta

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email")

@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ("date", "sender", "subject")

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ("id",)
    filter_horizontal = ("emails", "tags")

@admin.register(ThreadSummary)
class ThreadSummaryAdmin(admin.ModelAdmin):
    list_display = ("thread", "timestamp")

@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ("email", "action", "timestamp")

@admin.register(SpecificInstruction)
class SpecificInstructionAdmin(admin.ModelAdmin):
    list_display = ("contact", "tag", "instruction")


def _process_email(message, thread):
    """ This method will process one email
    parameters: message - a message returned from Gmail, thread: the Django thread object
    It assumes the thread already exists
    It will check the tags and create them if they don't exist
    It will save the email to the database
    """
    # Log that we process message id annd subject
    print(f"Processing message id: {message['id']} from: {message['From']} subject: {message['Subject']}")
    # check if the tags already exist in the database
    tags = message.get("labelIds", [])
    tag_objects = []
    for tag in tags:
        tag_obj, created = Tag.objects.get_or_create(name=tag) # type: ignore[attr-defined]
        tag_objects.append(tag_obj)

    # We check if the sender exists in the database and if not we create it
    sender_email = message.get("From")
    # if "<" in sender_email then we extract name or email; otherwise we assume just email for both name and email
    if "<" in sender_email:
        sender_name = sender_email.split("<")[0].strip()
        sender_email = sender_email.split("<")[1].split(">")[0].strip()
    else:
        sender_name = sender_email.strip()

    sender_obj, created = Contact.objects.get_or_create(
            email = sender_email,
            defaults = {
                "name": sender_name
                }
            )

    # check if the email already exists in the database
    # convert date from this sample format: Sun, 04 May 2025 07:01:00 +0000 to datetime
    # we will use the datetime module to parse the date
    message_date = datetime.strptime(message['Date'], "%a, %d %b %Y %H:%M:%S %z")
    email_obj, created = Email.objects.get_or_create(
        gmail_message_id=message['id'],
        defaults= {
            "gmail_thread_id" : thread.gmail_thread_id,
            "date": message_date,
            "subject": message['Subject'],
            "content": message['snippet'],
            "sender": sender_obj
            #"receiver": message['To'],
        }
    ) # type: ignore[attr-defined]
    # save tags
    #for tag_obj in tag_objects:
    #    email_obj.tags.add(tag_obj)

@admin.action(description="Fetch emails from Gmail")
def fetch_emails_from_gmail(modeladmin, request, queryset):
    """This will fetch emails from Gmail since the last sync
    For each email, it will check that:
        - labels (tags) already exist in the database. If not it will create them
        - thread already exist in the database. If not it will create them; and it will fetch all emails from that thread
        """
    # we retrieve the last sync time. If it does not exists then it default to now - 2 hours
    last_sync = SystemParameter.objects.filter(key="last_sync_time").first() # type: ignore[attr-defined]
    if not last_sync:
        last_sync = datetime.now() - timedelta(hours=2)
    else:
        last_sync = datetime.fromisoformat(last_sync.value)
    # log the last sync time
    print(f"Last sync time: {last_sync}")

    # fetch emails from gmail since last sync
    emails = gmail_helper.fetch_emails_since(last_sync)
    #log the number of emails fetched
    print(f"Fetched {len(emails)} emails since {last_sync}")

    # Now for each email we want to check if the thread already exists in the database
    # if not we will create it and fetch all emails from that thread
    for email in emails:
        # check if the thread already exists
        gmail_thread_id = email.get("threadId")
        thread, created = Thread.objects.get_or_create(gmail_thread_id=gmail_thread_id) # type: ignore[attr-defined]
        if created:
            # log that we created a new thread
            print(f"Created new thread with id {gmail_thread_id}")
            # fetch all emails from that thread
            thread_emails = gmail_helper.fetch_thread(gmail_thread_id)
            for thread_email in thread_emails['messages']:
                _process_email(thread_email, thread)
        else:
            email = gmail_helper.fetch_email(email['id'])
            _process_email(email, thread)

@admin.register(SystemParameter)
class SystemParameterAdmin(admin.ModelAdmin):
    list_display = ("key", "value")
    #We want to add a custom action to the SystemParameter admin
    actions = [fetch_emails_from_gmail]
