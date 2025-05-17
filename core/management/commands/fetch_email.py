# we will add a command to django manage.py to fetch emails from the gmail api
from django.core.management.base import BaseCommand
from core.models import SystemParameter, Thread, Email, Label, Contact, EmailAddress
from core.gmail_helper import gmail_helper
from datetime import datetime, timedelta
from pytz import timezone
import re

def _extract_email_and_name(email):
    """ This method will extract the email and name from the email string
    parameters: email - a string with the format "Name <email>"
    It will return a tuple with the name and email
    """
    if "<" in email:
        name = email.split("<")[0].strip()
        email = email.split("<")[1].split(">")[0].strip()
    else:
        name = email.strip()
    # remove any non-ascii characters
    name = name.encode('ascii', 'ignore').decode('ascii')
    email = email.encode('ascii', 'ignore').decode('ascii')
    # remove double spaces in name and hyphens
    name = re.sub(r'-', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    return (name, email)

def _get_or_create_contact(email_str):
    """Helper function to get or create Contact object"""
    name, email = _extract_email_and_name(email_str)
    
    contact = Contact.objects.filter(name=name).first()

    if contact:
        return contact

    # If not, then we search if we have a unique contact which already uses this email
    contacts = Contact.objects.filter(emails__email=email)
    if contacts.count() == 1:
        contact = contacts.first()
        return contact

    email_obj, created = EmailAddress.objects.get_or_create(
        email=email,
        defaults={
            "is_active": True,
            "is_generic": False
        }
    )

    # If we have multiple contacts with the same email, we create a new contact with the email and the name
    contact = Contact.objects.create(
        name=name,
    )
    contact.emails.add(email_obj)
    contact.save()

    return contact

def _process_email(message, thread):
    """ This method will process one email
    parameters: message - a message returned from Gmail, thread: the Django thread object
    It assumes the thread already exists
    It will check the labels and create them if they don't exist
    It will save the email to the database
    """
    # Log that we process message id and subject
    print(f"Processing message id: {message['id']} from: {message['From']} subject: {message['Subject']}")

    # Process sender
    sender_str = message.get("From")
    sender = _get_or_create_contact(sender_str)

    # Then we process the message
    message_date = datetime.fromtimestamp(int(message['internalDate']) / 1000)
    if message_date.tzinfo is None:
        message_date = message_date.replace(tzinfo=timezone('UTC'))
    print(f"Processing message date: %s --> %s" % (message['Date'], message_date.isoformat()))
    
    email_obj, created = Email.objects.get_or_create( 
        gmail_message_id=message['id'],
        defaults= {
            "gmail_thread_id": thread.gmail_thread_id,
            "date": message_date,
            "subject": message['Subject'],
            "snippet": message['snippet'],
            "sender": sender,
            "sender_str": sender_str,
            "body": message['Body'],
            "thread": thread,
        }
    )

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

    # Process "To"
    to = message.get("To", "")
    for receiver in to.split(","):
        if not receiver.strip():
            continue
        receiver_contact = _get_or_create_contact(receiver)
        email_obj.to_contacts.add(receiver_contact)

    # Process "Cc"
    cc = message.get("Cc", "")
    if cc:
        for receiver in cc.split(","):
            if not receiver.strip():
                continue
            receiver_contact = _get_or_create_contact(receiver)
            email_obj.cc_contacts.add(receiver_contact)

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
                    "value" : int(datetime.now().timestamp()) - 3600*12, #2 hours
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
