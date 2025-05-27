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