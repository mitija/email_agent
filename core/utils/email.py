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
    ]

    for indicator in calendar_indicators:
        if indicator in body:
            return True

    # Check for calendar file attachments
    if 'calendar.ics' in body or 'calendar.ical' in body:
        return True

    return False

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