# -*- coding: utf-8 -*-
"""
This module provides a helper class for LangGraph, which is used to create summaries of email threads.
and other things
"""
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
import re

class LangGraphHelper:
    def _thread_messages(self, thread):
        """
        Extract messages from the thread.
        """
        messages = []
        for email in thread.emails.all():
            # Assuming email has a 'body' attribute
            # We want to truncate the body to the first occurence of "On.*wrote:"
            # to avoid including the whole email thread in the summary
            # and only include the relevant part of the email
            # This is a simple regex to find the first occurrence of "On.*wrote:"
            # and truncate the body to that point
            truncated_body = re.sub(r"On.*wrote:", "", email.body, count=1)
            messages.append(truncated_body)
        return '\n'.join(messages)

    def create_thread_summary(self, thread):
        """
        Create a summary of the thread using LangGraph.
        """
        llm = Ollama(model="gemma3:4b-it-qat")
        conversation = self._thread_messages(thread)
        prompt = PromptTemplate.from_template(
            "This is not an interactive session. You must provide a summary of this conversation - no analysis or interpretation is required, just a summary of the content:\n{conversation}."
        )
        summary = llm.invoke(prompt.format(conversation=conversation))
        return summary

langgraph_helper = LangGraphHelper()
