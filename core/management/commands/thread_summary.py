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

class Command(BaseCommand):
    help = "Create a summary for each thread with more than 1 email and the label PERSONAL"
    
    def handle(self, *args, **options):
        """This will create a summary for each thread with more than 1 email and the label PERSONAL"""

        # Get all threads where the last email is CATEGRORY_PERSONAL and where there is not already a summary
        threads = Thread.objects.filter(
                last_email__labels__name="CATEGORY_PERSONAL",
                last_email__threadsummary__isnull=True
        ).distinct() # type: ignore[attr-defined]

        thread = threads.first() # we will only process the first thread for now
        if not thread:
            self.stdout.write(self.style.SUCCESS("No threads found")) # type: ignore[attr-defined]
            return
        self.stdout.write(self.style.SUCCESS(f"Thread ID: {thread.id} - Subject: {thread.subject} - Date: {thread.date}")) # type: ignore[attr-defined]

        # Now we create a summary for the thread
        langgraph_helper = get_langgraph_helper()
        summary_result = langgraph_helper.invoke({"thread": thread})
        
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
        with codecs.open('llm_prompts.log', 'a', encoding='utf-8') as f:
            f.write(f"=== {log_entry['timestamp']} - Thread Summary ===\n")
            f.write(f"Thread ID: {log_entry['thread_id']}\n")
            f.write(f"Subject: {log_entry['thread_subject']}\n")
            f.write(f"Date: {log_entry['thread_date']}\n")
            f.write("\nSummary:\n")
            f.write(json.dumps(log_entry['summary'], ensure_ascii=False, indent=2))
            f.write("\n\n" + "="*50 + "\n\n")




