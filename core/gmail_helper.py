import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import json

# this file will create a class calls GmailHelper,
# it will handle the authentication and fetching of emails and threads from Gmail
# authentication will be done using gmail authentication
# Methods will be
# fetch_emails_since (getting a timestamp as a parameter) - this will return email ids
# fetch_email - parameter email_id
# fetch_thread - parameter thread_id. This will return the thread object and the id of all emails in the thread

class GmailHelper:
    def __init__(self):
        self.creds = None
        self.service = None
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        self.authenticate()

    def authenticate(self):
        """ This function handles the OAuth2 authentication flow and returns the credentials."""
        # Load credentials if they exist
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)

        # If credentials are not valid, authenticate
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                # I am getting an error here, I want to authenticate using the console flow
                self.creds = flow.run_local_server(port=0)
            # Save credentials
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
        self.service = build('gmail', 'v1', credentials=self.creds)

    def fetch_emails_since(self, timestamp):
        """ This function fetches email IDs from Gmail since the given timestamp."""
        #if no timestamp then fetch emails since the last 10 minutes
        if not timestamp:
            timestamp = datetime.now() - timedelta(minutes=10)

        # Fetch messages ids from Gmail
        results = self.service.users().messages().list(userId='me', q=f'after:{int(timestamp.timestamp())}').execute() # type: ignore[attr-defined]
        messages = results.get('messages', [])
        return messages

    def fetch_email(self, email_id):
        """ This function fetches a single email from Gmail by its ID."""
        msg = self.service.users().messages().get(userId='me', id=email_id).execute() # type: ignore[attr-defined]
        # we will add keys From, Subject, To, Date to the msg object by searching through payload headers
        msg = self._find_common_headers(msg)
        return msg

    def fetch_label(self, label_id):
        """ This function fetches a label from Gmail by its ID. It caches known labels so we don't
        need to query the Gmail API every time."""
        # check if the label is already in the cache
        if hasattr(self, 'labels_cache') and label_id in self.labels_cache:
            return self.labels_cache[label_id]
        # if not, fetch it from the API
        label = self.service.users().labels().get(userId='me', id=label_id).execute() # type: ignore[attr-defined]
        # cache the label
        if not hasattr(self, 'labels_cache'):
            self.labels_cache = {}
        self.labels_cache[label_id] = label
        return label

    def fetch_thread(self, thread_id):
        """ This function fetches a thread from Gmail by its ID."""
        thread = self.service.users().threads().get(userId='me', id=thread_id).execute()
        # we will add keys From, Subject, To, Date to the msg object by searching through payload headers
        for msg in thread['messages']:
            msg = self._find_common_headers(msg)
        return thread

    def _find_common_headers(self, msg):
        headers = msg.get('payload', {}).get('headers', [])
        for header in headers:
            if header['name'] == 'From':
                msg['From'] = header['value']
            elif header['name'] == 'Subject':
                msg['Subject'] = header['value']
            elif header['name'] == 'To':
                msg['To'] = header['value']
            elif header['name'] == 'Date':
                msg['Date'] = header['value']
        return msg

gmail_helper = GmailHelper()

# write a main method that will test the fetch_emails_since method
if __name__ == "__main__":
    # fetch emails since 10 minutes ago
    timestamp = datetime.now() - timedelta(minutes=120)
    emails = gmail_helper.fetch_emails_since(timestamp)
    print("Fetched Emails: ", emails)
    # we want to have a set of the threadIds related to the emails downloaded
    thread_ids = set()
    for email in emails:
        msg = gmail_helper.fetch_email(email['id'])
        thread_ids.add(msg['threadId'])

    # then we want to print all the emails for each thread
    for thread_id in thread_ids:
        print("===> Thread ID: ", thread_id)
        # Fetch all emails in the thread
        thread = gmail_helper.fetch_thread(thread_id)
        print("Thread labels", thread.get('labelIds', ''))
        for email in thread['messages']:
            print("Email ID: ", email['id'])
            print("From: ", email['From'])
            print("To: ", email['To'])
            print("Date: ", email['Date'])
            print("Labels: ", email.get('labelIds', ''))
            print("Subject: ", email['Subject'])
            print("Email Snippet: ", email['snippet'])
            print("\n")


