# -*- coding: utf-8 -*-
"""
This module provides a helper class for LangGraph, which is used to create summaries of email threads.
and other things
"""
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
import re

class LangGraphHelper:
    def _thread_messages(self, thread):
        """
        Extract messages from the thread.
        """
        messages = []
        for email in thread.email_set.all():
            # Assuming email has a 'body' attribute
            # We want to truncate the body to the first occurence of "On.*wrote:"
            # to avoid including the whole email thread in the summary
            # and only include the relevant part of the email
            # This is a simple regex to find the first occurrence of "On.*wrote:"
            # and truncate the body to that point
            truncated_body = re.sub(r"On.*wrote:", "", email.body, count=1)
            messages.append("From: %s <%s>: " % (email.sender.name, email.sender.email))
            messages.append("To: %s: " % email.to)
            messages.append("Date: %s: " % email.date)
            messages.append("Labels: %s: " % " ".join([l.name for l in email.labels.all()]))
            messages.append("Subject: %s: " % email.subject)
            messages.append(truncated_body)
            messages.append("----")
        return '\n'.join(messages)

    def create_thread_summary(self, thread):
        """
        Create a summary of the thread using LangGraph.
        """
        llm = OllamaLLM(model="gemma3:4b-it-qat")
        conversation = self._thread_messages(thread)
        prompt_text = """
This is not an interactive session. You must read this conversation and assess:
- a summary
- participants and what we can infer about these participants, in particular the company they work for, their job, and their role in the discussion
- what action to be done: Ignore, Need to Know, Need to respond
- reason for providing that action recommendation

Here is the conversation:
{conversation}

Please return your answer strictly in JSON format using the following schema:
{{
  "action": "IGNORE | NEED_TO_KNOW | NEED_TO_RESPOND",
  "summary": "a short summary of the conversation",
  "participants: [ {{ "email": "email address", "relevant information": "relevant information about this person gained from the thread" }}, ],
    "rationale": "a short explanation of why you chose this action"
}}
            """

        #The below does not work - how to fix it
        prompt = PromptTemplate.from_template(
                prompt_text,
        )
        text = prompt.format(conversation=conversation)
        print("Prompt: ", text)
        summary = llm.invoke(prompt.format(conversation=conversation))
        return summary

langgraph_helper = LangGraphHelper()
