# -*- coding: utf-8 -*-
# This file will add a command to manage.py to identify an email where:
# - the label PERSONAL is present
# - it belongs to a thread with more than 1 email
#- the email is not already attached to a thread summary
from django.core.management.base import BaseCommand
from core.models import Thread, ThreadSummary
from core.llm import get_langgraph_helper


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
        summary = langgraph_helper.invoke({"thread": thread})




