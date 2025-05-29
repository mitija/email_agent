import re

def is_calendar_invite(subject, body, headers=None):
    """Check if an email is a calendar invite or attendance notification.
    
    Args:
        subject (str): The email subject
        body (str): The email body
        headers (list, optional): List of header dicts with 'name' and 'value' keys
        
    Returns:
        bool: True if the email appears to be a calendar-related message
    """
    # Check headers if available
    if headers:
        for header in headers:
            header_name = header.get('name', '').lower()
            header_value = header.get('value', '').lower()
            
            # Check Microsoft calendar headers
            if header_name in [
                'x-microsoft-cdo-busystatus',
                'x-microsoft-cdo-intendedbusystatus',
                'x-microsoft-cdo-all-day-event',
                'x-microsoft-cdo-instance-type',
                'x-microsoft-cdo-importance',
                'x-microsoft-cdo-appt-sequence',
                'x-microsoft-cdo-appt-state'
            ]:
                return True
                
            # Check content class
            if header_name == 'content-class' and header_value == 'urn:content-classes:calendarmessage':
                return True
                
            # Check message class
            if header_name == 'x-microsoft-cdo-message-class' and 'calendar' in header_value:
                return True

    # Check subject for calendar response indicators
    subject = subject.lower().strip()
    subject_indicators = [
        'accepted',
        'declined',
        'tentative',
        'canceled',
        'cancelled',
        'updated',
        'rescheduled',
        're-scheduled',
        'postponed',
        'moved',
        'changed',
    ]
    
    # Check if subject starts with any of the indicators (with or without colon)
    for indicator in subject_indicators:
        if subject.startswith(indicator) or subject.startswith(f"{indicator}:"):
            return True

    print(f"Subject: {subject}")
    print("Not seen as a calendar invite")

    # Check body for calendar-related content
    body = body.lower()
    calendar_indicators = [
        'calendar invitation',
        'calendar event',
        'meeting invitation',
        'meeting request',
        'invitation to',
        'invited you to',
        'invited to a meeting',
        'invited to the meeting',
        'invited to meeting',
        'has accepted this invitation',
        'has declined this invitation',
        'has tentatively accepted this invitation',
        'has responded to this invitation',
        'accepted:',
        'declined:',
        'tentative:',
        'when:',
        'where:',
        'organizer:',
        'attendees:',
        'calendar.ics',
        'calendar.ical',
        'calendar.vcs',
        'calendar.vcal',
        'calendar.ifb',
        'calendar.ifc',
        'calendar.ifd',
        'calendar.ifg',
        'calendar.ifh',
        'calendar.ifi',
        'calendar.ifj',
        'calendar.ifk',
        'calendar.ifl',
        'calendar.ifm',
        'calendar.ifn',
        'calendar.ifo',
        'calendar.ifp',
        'calendar.ifq',
        'calendar.ifr',
        'calendar.ifs',
        'calendar.ift',
        'calendar.ifu',
        'calendar.ifv',
        'calendar.ifw',
        'calendar.ifx',
        'calendar.ify',
        'calendar.ifz',
    ]

    for indicator in calendar_indicators:
        if indicator in body:
            return True

    # Check for calendar file attachments
    if 'calendar.ics' in body or 'calendar.ical' in body:
        return True

    return False

def normalize_whitespace(text):
    """Normalize whitespace in text by replacing special Unicode spaces and normalizing empty lines.
    
    Args:
        text (str): The text to normalize
        
    Returns:
        str: The normalized text with standard spaces and normalized empty lines
    """
    # Dictionary of Unicode spaces and their replacements
    UNICODE_SPACES = {
        '\u00A0': ' ',    # NO-BREAK SPACE
        '\u1680': ' ',    # OGHAM SPACE MARK
        '\u2000': ' ',    # EN QUAD
        '\u2001': ' ',    # EM QUAD
        '\u2002': ' ',    # EN SPACE
        '\u2003': ' ',    # EM SPACE
        '\u2004': ' ',    # THREE-PER-EM SPACE
        '\u2005': ' ',    # FOUR-PER-EM SPACE
        '\u2006': ' ',    # SIX-PER-EM SPACE
        '\u2007': ' ',    # FIGURE SPACE
        '\u2008': ' ',    # PUNCTUATION SPACE
        '\u2009': ' ',    # THIN SPACE
        '\u200A': ' ',    # HAIR SPACE
        '\u200B': '',     # ZERO WIDTH SPACE
        '\u200C': '',     # ZERO WIDTH NON-JOINER
        '\u200D': '',     # ZERO WIDTH JOINER
        '\u202F': ' ',    # NARROW NO-BREAK SPACE
        '\u205F': ' ',    # MEDIUM MATHEMATICAL SPACE
        '\u3000': ' ',    # IDEOGRAPHIC SPACE
        '\uFEFF': '',     # ZERO WIDTH NO-BREAK SPACE (BOM)
        '\u180E': '',     # MONGOLIAN VOWEL SEPARATOR
        '&nbsp;': ' ',    # HTML NO-BREAK SPACE
        '\u2028': '\n',   # LINE SEPARATOR
        '\u2029': '\n\n', # PARAGRAPH SEPARATOR
        '\u2060': '',     # WORD JOINER
        '\u2061': '',     # FUNCTION APPLICATION
        '\u2062': '',     # INVISIBLE TIMES
        '\u2063': '',     # INVISIBLE SEPARATOR
        '\u2064': '',     # INVISIBLE PLUS
        '\u206A': '',     # INHIBIT SYMMETRIC SWAPPING
        '\u206B': '',     # ACTIVATE SYMMETRIC SWAPPING
        '\u206C': '',     # INHIBIT ARABIC FORM SHAPING
        '\u206D': '',     # ACTIVATE ARABIC FORM SHAPING
        '\u206E': '',     # NATIONAL DIGIT SHAPES
        '\u206F': '',     # NOMINAL DIGIT SHAPES
        '\u200E': '',     # LEFT-TO-RIGHT MARK
        '\u200F': '',     # RIGHT-TO-LEFT MARK
        '\u202A': '',     # LEFT-TO-RIGHT EMBEDDING
        '\u202B': '',     # RIGHT-TO-LEFT EMBEDDING
        '\u202C': '',     # POP DIRECTIONAL FORMATTING
        '\u202D': '',
        '\u202E': '',     # RIGHT-TO-LEFT OVERRIDE
        '\u034F': '',     # COMBINING GRAPHEME JOINER
    }

    # Replace all special space characters
    for space, replacement in UNICODE_SPACES.items():
        text = text.replace(space, replacement)

    # Replace two or more empty lines with only one empty line
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text 