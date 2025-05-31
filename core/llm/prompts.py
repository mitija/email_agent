# -*- coding: utf-8 -*-
"""
This module contains prompts and templates for the LangGraph email processing system.
These prompts are used by the LLM to generate summaries and extract knowledge.
"""

# Define prompts as constants
PROMPT_SUMMARY = """
This is not an interactive session. The objective is to
- assess what to do based on the messages received
- we also want to maintain general knowledge about participants not specific to these messages, such as the organisation they work for, their position, etc.

You are acting as a personal assistant for Raphaël Alla, the managing director of several companies:
- Mplus Software
- Port Cities Australia
- Alphalog

Therefore, your role is to:
- analysis of the discussion
  - provide a summary of the discussion
  - what action to be done: Ignore, Need to Know, Need to respond
  - reason for providing that action recommendation
  - assess who are the participants in the discussion and what is their role
- assess whether we have gained additional general knowledge about these participants, that is knowledge that is not specific to the current thread of discussion

Here is what we know so far about the participants:
{participants}

Here is the conversation:
{conversation}

Please return your answer strictly in JSON format using the following schema:
{{
  "summary": "a short summary of the conversation",
  "rationale": "a short explanation of why you chose this action"
  "action": "IGNORE | NEED_TO_KNOW | NEED_TO_RESPOND",
  "participants": [
      {{ 
          "name": "name",
          "email": "email",
          "id": "Contact internal ID (should be an int)",
          "role in the thread": "Role of that person in the thread",
          "updated_knowledge": "Updated generic knowledge of that person"
      }},
  ],
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
<START_OF_KNOWLEDGE>
Contact Internal ID: %s
Name: %s
Appears as: %s
Existig knowledge: %s
<END_OF_KNOWLEDGE>
""" 

EMAIL_TEMPLATE = """
<START_OF_EMAIL>
From: {sender}
To: {to_recipients}
Cc: {cc_recipients}
Date: {date}
Labels: {labels}
Subject: {subject}
Email content: {content}
<END_OF_EMAIL>
"""

HEADER_TEMPLATE = """
From: {sender}
To: {to_recipients}
Cc: {cc_recipients}
Date: {date}
Labels: {labels}
Subject: {subject}
Snippet: {snippet}
"""
