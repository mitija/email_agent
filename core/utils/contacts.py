import re
import unicodedata
from django.db import models
from core.models import Contact

def extract_email_and_name(original_string):
    """Extract email and name from the email string.
    
    Args:
        original_string (str): A string with the format "Name <email>"
        
    Returns:
        tuple: A tuple containing (name, email)
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

    # Normalize the name
    name = re.sub(r'-', ' ', name)
    name = re.sub(r'\.', ' ', name)
    name = re.sub(r'_', ' ', name)
    name = re.sub(r'\'', ' ', name)  # in some languages, ' is used as an apostrophe

    # Remove quotes from name
    name = re.sub(r'"', '', name)
    name = name.strip()

    # Remove any non-ascii characters and replace them by their ascii equivalent
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')

    # Remove double spaces in name
    name = re.sub(r'\s+', ' ', name)
    # Capitalize each word in name
    name = name.title()

    return (name, email)

def search_similar_contacts(name, email):
    """Search for similar contacts based on name and email.
    
    Args:
        name (str): The contact's name
        email (str): The contact's email
        
    Returns:
        Contact or None: The matching contact if found, None otherwise
    """
    # First search for the same normalized name and email
    possible_contacts = Contact.objects.filter(name=name, emails__email=email)
    if len(possible_contacts) == 1:
        contact = possible_contacts.first()
        return contact
    elif len(possible_contacts) > 1:
        return None

    # If not found, search for the same normalized name
    possible_contacts = Contact.objects.filter(name=name)
    if len(possible_contacts) == 1:
        contact = possible_contacts.first()
        return contact
    elif len(possible_contacts) > 1:
        return None

    # If we have not found anyone
    return None 