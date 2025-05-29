import re
import unicodedata
from django.db import models
from .base import TimestampedModel
from .contact import Contact

def extract_email_and_name(original_string):
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
    name = re.sub(r'\'', ' ', name) # in some languages, ' is used as an apostrophe

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

def search_similar_contacts(name, email):
    # first we will search for the same normalized name and email
    print(f"CONTACT: Searching for similar contacts for {name} and {email}")
    possible_contacts = Contact.objects.filter(name=name, emails__email=email)
    if len(possible_contacts) == 1:
        contact = possible_contacts.first()
        print(f"CONTACT: Found contact {contact} for {name} and {email}")
        return contact
    elif len(possible_contacts) > 1:
        print(f"CONTACT: MULTIPLE CONTACTS FOUND for {name} and {email}: {possible_contacts}")
        return None

    # if not, we will search for the same normalized name
    possible_contacts = Contact.objects.filter(name=name)
    if len(possible_contacts) == 1:
        contact = possible_contacts.first()
        print(f"CONTACT Found contact {contact} for {name}")
        return contact
    elif len(possible_contacts) > 1:
        print(f"CONTACT: MULTIPLE CONTACTS FOUND for {name}: {possible_contacts}")

    # If we have not found anyone
    return None

def remove_quoted_text(body: str) -> str:
    """Removes quoted text from email body.
    
    Handles various email client quote patterns including:
    - "On ... wrote:" (Gmail)
    - "From: ... Sent: ... To: ... Subject: ..." (Outlook)
    - "> " (common quote marker)
    - "-----Original Message-----" (Outlook)
    - Outlook header pattern with From, Sent, To, Cc, Subject
    
    Args:
        body (str): The email body text
        
    Returns:
        str: The email body without quoted text
    """
    # First, try to find the last occurrence of common quote markers
    patterns = [
        r"On.*wrote:",  # Gmail style
        r"From:.*\nSent:.*\nTo:.*\nSubject:",  # Outlook style
        r"-----Original Message-----",  # Outlook style
        r"^>.*$",  # Common quote marker
        r"From:.*\nSent:.*\nTo:.*\n(?:Cc:.*\n)?Subject:",  # Outlook header pattern
    ]
    
    # Find the earliest occurrence of any quote pattern
    earliest_quote = len(body)
    for pattern in patterns:
        matches = list(re.finditer(pattern, body, re.MULTILINE))
        if matches:
            earliest_quote = min(earliest_quote, matches[0].start())
    
    # Return only the content before the first quote
    return body[:earliest_quote].strip() 