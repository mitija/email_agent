# -*- coding: utf-8 -*-
"""
This module contains prompts and templates for the LangGraph email processing system.
These prompts are used by the LLM to generate summaries and extract knowledge.
"""

# Define prompts as constants
PROMPT_SUMMARY = """
This is not an interactive session. You must read this conversation and assess:
- a summary
- participants and what we can infer about these participants, in particular the company they work for, their job, and their role in the discussion
- what action to be done: Ignore, Need to Know, Need to respond
- reason for providing that action recommendation

Here is what we know about the participants:
{participants}

Here is the conversation:
{conversation}

Please return your answer strictly in JSON format using the following schema:
{{
  "action": "IGNORE | NEED_TO_KNOW | NEED_TO_RESPOND",
  "summary": "a short summary of the conversation",
  "participants": [
      {{ 
          "name": "name",
          "id": "Contact internal ID (should be an int)",
          "relevant information": "relevant information about this person gained from the thread" 
      }},
  ],
  "rationale": "a short explanation of why you chose this action"
}}
"""

PROMPT_PARTICIPANT_KNOWLEDGE = """
In the current thread of discussion, we have the followig message history and summary of discussion:
Thread subject: {thread_subject}
Summary of messages: {message_headers}
Thread summary {thread_summary}

We have gathered that the participants and their role is:
{participants_information}

We maintain general knowledge about people we interact with. Each time we receive an email, we want to update that general information if needed. 
Here is what we already know about {contact_name}:
    {previous_knowledge}

What is the updated knowledge we have about {contact_name}.

Return your answer strictly in JSON format using the following format:
{{ "updated_knowledge": "updated knowledge" }}
"""

KNOWLEDGE_TEMPLATE = """
Contact Internal ID: %s
Name: %s
Appears as: %s
Existig knowedge: %s
""" 