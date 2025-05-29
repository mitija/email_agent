# -*- coding: utf-8 -*-
# This file will add a command to manage.py to identify an email where:
# - the label PERSONAL is present
# - it belongs to a thread with more than 1 email
#- the email is not already attached to a thread summary
from django.core.management.base import BaseCommand
from core.models import Thread, ThreadSummary
from core.llm import get_langgraph_helper
import json
import logging
from datetime import datetime
import codecs

# Configure logging with UTF-8 encoding
logging.basicConfig(
    filename='llm_prompts.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    encoding='utf-8'
)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Create a summary for each thread with more than 1 email and the label PERSONAL"
    
    def handle(self, *args, **options):
        """This will create a summary for each thread with more than 1 email and the label PERSONAL"""

        # Get all threads where the last email has CATEGORY_PERSONAL label but not CALENDAR label
        # and where there is not already a summary
        threads = Thread.objects.filter(
                last_email__labels__name="CATEGORY_PERSONAL"
        ).exclude(
                last_email__labels__name="Calendar"
        ).filter(
                last_email__threadsummary__isnull=True
        ).distinct() # type: ignore[attr-defined]

        thread = threads.first() # we will only process the first thread for now
        if not thread:
            self.stdout.write(self.style.SUCCESS("No threads found")) # type: ignore[attr-defined]
            return

        # Log thread details and emails
        logger.info(f"Processing Thread - ID: {thread.id}, Subject: {thread.subject}")
        logger.info("Emails in thread:")
        for email in thread.email_set.all():
            labels = [label.name for label in email.labels.all()]
            logger.info(f"- Email ID: {email.id}, From: {email.sender_str}, Subject: {email.subject}, Date: {email.date}")
            logger.info(f"  Labels: {', '.join(labels) if labels else 'None'}")

        self.stdout.write(self.style.SUCCESS(f"Thread ID: {thread.id} - Subject: {thread.subject} - Date: {thread.date}")) # type: ignore[attr-defined]

        # Now we create a summary for the thread
        langgraph_helper = get_langgraph_helper()
        result = langgraph_helper.invoke({"thread": thread})
        summary_result = result["thread_summary"]
        
        # Extract only the serializable summary data
        summary_data = {
            'summary': summary_result.get('summary', ''),
            'action': summary_result.get('action', ''),
            'rationale': summary_result.get('rationale', ''),
            'participants': summary_result.get('participants', [])
        }
        
        # Log the summary in a human-readable format
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'thread_id': thread.id,
            'thread_subject': thread.subject,
            'thread_date': thread.date.isoformat(),
            'summary': summary_data
        }
        
        # Write to log file with proper formatting
        log_message = (
            f"=== {log_entry['timestamp']} - Thread Summary ===\n"
            f"Thread ID: {log_entry['thread_id']}\n"
            f"Subject: {log_entry['thread_subject']}\n"
            f"Date: {log_entry['thread_date']}\n"
            f"\nSummary:\n"
            f"{summary_data['summary']}\n"
            f"\nAction: {summary_data['action']}\n"
            f"\nRationale: {summary_data['rationale']}\n"
            f"\nParticipants:\n"
            f"{json.dumps(summary_data['participants'], indent=2, ensure_ascii=False)}\n"
            f"\n{'='*50}\n\n"
        )
        logger.info(log_message)

        # Display summary in console
        self.stdout.write(self.style.SUCCESS("\nThread Summary:"))
        self.stdout.write(f"\nSummary: {summary_data['summary']}")
        self.stdout.write(f"\nAction: {summary_data['action']}")
        self.stdout.write(f"\nRationale: {summary_data['rationale']}")
        self.stdout.write("\n\nParticipants:")
        for participant in summary_data['participants']:
            self.stdout.write(f"\n- {participant['name']} ({participant['email']})")
            self.stdout.write(f"  Role: {participant['role in the thread']}")
            self.stdout.write(f"  Updated Knowledge: {participant['updated_knowledge']}")




