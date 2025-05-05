# we will add a command to django manage.py to fetch emails from the gmail api
from django.core.management.base import BaseCommand
from core.models import SystemParameter, Thread, Email, Label, Contact
from core.gmail_helper import gmail_helper
from datetime import datetime, timedelta
import base64

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
    return (name, email)


def _extract_body_from_gmail_message(payload):
    text_body = None
    html_body = None

    def extract_parts(parts):
        nonlocal text_body, html_body
        for part in parts:
            mime_type = part.get("mimeType")
            body = part.get("body", {})
            data = body.get("data")
            if data:
                decoded = base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")
                if mime_type == "text/html" and not html_body:
                    html_body = decoded
                elif mime_type == "text/plain" and not text_body:
                    text_body = decoded
            # Recursively handle nested multiparts
            if "parts" in part:
                extract_parts(part["parts"])

    if payload.get("mimeType", "").startswith("multipart/"):
        extract_parts(payload["parts"])
    else:
        # Single-part message
        data = payload.get("body", {}).get("data")
        if data:
            decoded = base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")
            if payload["mimeType"] == "text/html":
                html_body = decoded
            elif payload["mimeType"] == "text/plain":
                text_body = decoded

    return html_body or text_body or ""


def _process_email(message, thread):
    """ This method will process one email
    parameters: message - a message returned from Gmail, thread: the Django thread object
    It assumes the thread already exists
    It will check the labels and create them if they don't exist
    It will save the email to the database
    """
    # Log that we process message id annd subject
    print(f"Processing message id: {message['id']} from: {message['From']} subject: {message['Subject']}")

    # We check if the sender exists in the database and if not we create it
    sender_email = message.get("From")
    sender_name, sender_email = _extract_email_and_name(sender_email)

    sender_obj, created = Contact.objects.get_or_create(
            email = sender_email,
            defaults = {
                "name": sender_name
                }
            )

    # Then we process the message
    message_date = datetime.fromtimestamp(int(message['internalDate']) / 1000)
    message_body = _extract_body_from_gmail_message(message['payload'])
    print(f"Processing message date: %s --> %s" % (message['Date'], message_date.isoformat()))
    email_obj, created = Email.objects.get_or_create( 
        gmail_message_id=message['id'],
        defaults= {
            "gmail_thread_id" : thread.gmail_thread_id,
            "date": message_date,
            "subject": message['Subject'],
            "snippet": message['snippet'],
            "sender": sender_obj,
            "body": message_body,
        }
    ) # type: ignore[attr-defined]

    thread.emails.add(email_obj) # type: ignore[attr-defined]

    # Process labels
    labels = message.get("labelIds", [])
    for gmail_label_id in labels:
        label = gmail_helper.fetch_label(gmail_label_id)
        label_obj, created = Label.objects.get_or_create(
                gmail_label_id=label["id"],
                defaults={
                    "name" :label["name"],
                    }
                ) # type: ignore[attr-defined]
        # add the label to the email object
        email_obj.labels.add(label_obj) # type: ignore[attr-defined]

    # Process "To"
    to = message.get("To")
    for receiver in to.split(","):
        receiver_name, receiver_email = _extract_email_and_name(receiver)
        # check if the receiver exists in the database and if not we create it
        receiver_obj, created = Contact.objects.get_or_create(
            email = receiver_email,
            defaults = {
                "name": receiver_name
                }
            )
        # add the receiver to the email object
        email_obj.to.add(receiver_obj) # type: ignore[attr-defined]

    # Process "Cc"
    cc = message.get("Cc", False)
    if cc:
        for receiver in cc.split(","):
            receiver_name, receiver_email = _extract_email_and_name(receiver)
            # check if the receiver exists in the database and if not we create it
            receiver_obj, created = Contact.objects.get_or_create(
                email = receiver_email,
                defaults = {
                    "name": receiver_name
                    }
                )
            # add the receiver to the email object
            email_obj.cc.add(receiver_obj) # type: ignore[attr-defined]


class Command(BaseCommand):
    help = "Fetch emails from Gmail and store them in the database"

    def handle(self, *args, **options):
        """This will fetch emails from Gmail since the last sync
        For each email, it will check that:
            - labels already exist in the database. If not it will create them
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
