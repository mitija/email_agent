import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import bleach
import markdownify
import base64
import re
from .utils import normalize_whitespace

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

    md_body = None
    text_body = None
    if payload.get("mimeType", "").startswith("multipart/"):
        extract_parts(payload["parts"])
    else:
        # Single-part message
        data = payload.get("body", {}).get("data")
        if data:
            decoded = base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")
            if payload["mimeType"] == "text/html":
                # First clean the HTML and remove display:none elements
                cleaned_html = bleach.clean(decoded, 
                    strip=False,
                    tags=['div', 'span', 'p', 'br', 'b', 'i', 'u', 'em', 'strong', 'a', 'ul', 'ol', 'li', 'blockquote', 'pre', 'code', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'tr', 'td', 'th', 'thead', 'tbody'],
                    attributes={'*': ['style', 'class', 'id', 'href', 'src', 'alt', 'title']}
                )
                # Remove elements with display:none
                cleaned_html = re.sub(r'<[^>]*style="[^"]*display:\s*none[^"]*"[^>]*>.*?</[^>]*>', '', cleaned_html, flags=re.DOTALL)
                # Convert to markdown
                md_body = markdownify.markdownify(cleaned_html)
            elif payload["mimeType"] == "text/plain":
                text_body = decoded
    body = text_body or md_body or ""

    # Normalize whitespace in the body
    body = normalize_whitespace(body)

    return body

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
        # Fetch messages ids from Gmail. Handle the next page token if needed
        results = self.service.users().messages().list(userId='me', q=f'after:{int(timestamp)+1}', maxResults = 100).execute() # type: ignore[attr-defined]
        messages = results.get('messages', [])
        while 'nextPageToken' in results:
            page_token = results['nextPageToken']
            results = self.service.users().messages().list(userId='me', q=f'after:{int(timestamp)+1}', pageToken=page_token).execute() # type: ignore[attr-defined]
            messages.extend(results.get('messages', []))

        # We want to reverse the order of the messages so that the oldest messages are first
        messages.reverse()

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
            elif header['name'] == 'Cc':
                msg['Cc'] = header['value']
            elif header['name'] == 'Date':
                msg['Date'] = header['value']

        msg['Body'] = _extract_body_from_gmail_message(msg['payload'])

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


