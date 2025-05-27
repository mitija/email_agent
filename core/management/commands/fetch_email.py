# we will add a command to django manage.py to fetch emails from the gmail api
from django.core.management.base import BaseCommand
from core.models import SystemParameter, Thread, Email, Label, Contact, EmailAddress, EmailString
from core.gmail_helper import gmail_helper
from core.utils import is_calendar_invite
from datetime import datetime, timedelta
from pytz import timezone
import re
import unicodedata

def _process_email(message, thread):
    """ This method will process one email
    parameters: message - a message returned from Gmail, thread: the Django thread object
    It assumes the thread already exists
    It will check the labels and create them if they don't exist
    It will save the email to the database
    """
    # Log that we process message id and subject
    print(f"Processing message id: {message['id']} from: {message['From']} subject: {message['Subject']}")

    to_str = message.get("To", "").strip()
    cc_str = message.get("Cc", "").strip()

    # Then we create the email object
    message_date = datetime.fromtimestamp(int(message['internalDate']) / 1000)
    if message_date.tzinfo is None:
        message_date = message_date.replace(tzinfo=timezone('UTC'))
    print(f"Processing message date: %s --> %s" % (message['Date'], message_date.isoformat()))

    sender_str = message.get("From", "").strip()
    sender_str_obj, created = EmailString.objects.get_or_create(
        original_string=sender_str,
    )
    
    email_obj, created = Email.objects.get_or_create( 
        gmail_message_id=message['id'],
        defaults= {
            "gmail_thread_id": thread.gmail_thread_id,
            "date": message_date,
            "subject": message['Subject'],
            "snippet": message['snippet'],
            "body": message['Body'],
            "thread": thread,
            "sender_str": sender_str_obj,
        }
    )

    # Process to and from fields
    for receiver in to_str.split(","):
        if not receiver.strip():
            continue
        receiver_str_obj, created = EmailString.objects.get_or_create(
            original_string=receiver.strip(),
        )
        email_obj.to_str.add(receiver_str_obj)

    for receiver in cc_str.split(","):
        if not receiver.strip():
            continue
        receiver_str_obj, created = EmailString.objects.get_or_create(
            original_string=receiver.strip(),
        )
        email_obj.cc_str.add(receiver_str_obj)

    thread.last_email = email_obj
    thread.save()

    # Process labels
    labels = message.get("labelIds", [])
    for gmail_label_id in labels:
        label = gmail_helper.fetch_label(gmail_label_id)
        label_obj, created = Label.objects.get_or_create(
            gmail_label_id=label["id"],
            defaults={
                "name": label["name"],
            }
        )
        email_obj.labels.add(label_obj)

    # Check if this is a calendar invite and add the Calendar label if needed
    if is_calendar_invite(
        subject=message['Subject'],
        body=message['Body'],
        headers=message.get('payload', {}).get('headers', [])
    ):
        calendar_label, created = Label.objects.get_or_create(
            name="Calendar",
            defaults={
                "gmail_label_id": "CALENDAR",  # This is a custom label, not a Gmail system label
            }
        )
        email_obj.labels.add(calendar_label)

    email_obj.save()


class Command(BaseCommand):
    help = "Fetch emails from Gmail and store them in the database"

    def handle(self, *args, **options):
        """This will fetch emails from Gmail since the last sync
        For each email, it will check that:
            - labels already exist in the database. If not it will create them
            - thread already exist in the database. If not it will create them; and it will fetch all emails from that thread
            """
        # we retrieve the last sync time. If it does not exists then it default to now - 2 hours
        last_sync_obj, created = SystemParameter.objects.get_or_create(
                key="last_sync_time",
                defaults= {
                    "value" : int(datetime.now().timestamp()) - 3600*24, #2 hours
                    }
                ) # type: ignore[attr-defined]
        # log the last sync time
        print(f"Last sync time: {last_sync_obj.value}")

        # fetch emails from gmail since last sync
        emails = gmail_helper.fetch_emails_since(int(last_sync_obj.value) + 1)
        #log the number of emails fetched
        print(f"Fetched {len(emails)} emails since {last_sync_obj.value}")

        if not emails:
            print("No new emails to process")
            return

        # Now for each email we want to check if the thread already exists in the database
        # if not we will create it and fetch all emails from that thread
        max_timestamp = 0
        for email_record in emails:
            # check if the thread already exists
            gmail_thread_id = email_record.get("threadId")
            thread, created = Thread.objects.get_or_create(gmail_thread_id=gmail_thread_id) # type: ignore[attr-defined]
            if created:
                # log that we created a new thread
                print(f"Created new thread with id {gmail_thread_id}")
                # fetch all emails from that thread
                thread_emails = gmail_helper.fetch_thread(gmail_thread_id)
                for thread_email in thread_emails['messages']:
                    _process_email(thread_email, thread)
                    # We don't update max timestamp for threaded emails as this may fetch newer emails and we don't want to miss emails in case the process stops in the middle
                    # max_timestamp = max(int(thread_email['internalDate'])/1000, max_timestamp)
            else:
                email = gmail_helper.fetch_email(email_record['id'])
                _process_email(email, thread)
                max_timestamp = max(int(email['internalDate'])/1000, max_timestamp)

        # update the last sync time
        last_sync_obj.value = int(max_timestamp)
        last_sync_obj.save()
