from collections import Counter
from typing import List, Dict, Any
from core.models import Thread, Email

def get_thread_participants(thread: Thread) -> tuple[List[str], List[str]]:
    """
    Get active and other participants from a thread.
    Returns a tuple of (active_participants, other_participants)
    """
    all_participants = []
    for email in thread.email_set.all():
        all_participants.append(email.sender_str.original_string)
        all_participants.extend([to.original_string for to in email.to_str.all()])
        all_participants.extend([cc.original_string for cc in email.cc_str.all()])
    
    # Count participant frequency
    participant_counts = Counter(all_participants)
    
    # Get active participants (those who appear more than once)
    active_participants = [p for p, count in participant_counts.items() if count > 1]
    
    # Get other participants (those who appear only once)
    other_participants = [p for p, count in participant_counts.items() if count == 1]
    
    return sorted(active_participants), sorted(other_participants)

def enhance_thread_data(thread: Thread, include_summary: bool = False) -> Dict[str, Any]:
    """
    Enhance thread data with additional information.
    Returns a dictionary with enhanced thread data.
    """
    first_email = thread.email_set.order_by('date').first()
    last_email = thread.last_email
    
    # Get all tags/labels from emails in the thread
    tags = set()
    for email in thread.email_set.all():
        tags.update(label.name for label in email.labels.all())
    tags = sorted(list(tags))
    
    # Get participant information
    active_participants, other_participants = get_thread_participants(thread)
    
    enhanced_data = {
        'id': thread.id,
        'date': first_email.date if first_email else None,
        'subject': thread.subject,
        'snippet': last_email.snippet if last_email else '',
        'tags': tags,
        'first_message_date': first_email.date if first_email else None,
        'last_message_date': last_email.date if last_email else None,
        'initiated_by': first_email.sender_str.original_string if first_email else None,
        'active_participants': active_participants,
        'other_participants': other_participants,
    }
    
    if include_summary:
        from core.models import ThreadSummary
        latest_summary = ThreadSummary.objects.filter(thread=thread).order_by('-timestamp').first()
        enhanced_data.update({
            'summary': latest_summary.summary if latest_summary else None,
            'action': latest_summary.action if latest_summary else None,
            'rationale': latest_summary.rationale if latest_summary else None,
            'has_summary': latest_summary is not None,
        })
    
    return enhanced_data 