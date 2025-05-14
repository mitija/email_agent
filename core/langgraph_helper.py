# -*- coding: utf-8 -*-
"""
This module provides a helper class for LangGraph, which is used to create summaries of email threads.
and other things
"""
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
import json

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
  "participants: [ {{ "name": "name", "email": "email address if known or N/A", "relevant information": "relevant information about this person gained from the thread" }}, ],
    "rationale": "a short explanation of why you chose this action"
}}
"""

PROMPT_PARTICIPANT_KNOWLEDGE = """
What we knew about this person:
    {previous_knowledge}
What we have learnt about this person in the latest email thread:
Thread summary {thread_summary}
New knowledge: {new_knowledge}

What is the updated knowledge we have about this person.

Return your answer strictly in JSON format using the following format:
{{ "updated_knowledge": "updated knowledge" }}
"""

def sanitize_json(text):
    """
    Extract JSON from the text.
    This function will remove any character before the first '{' character and the last '}'
    """
    # Remove any character before the first '{' character and the last '}'
    text = text[text.find('{'):]
    text = text[:text.rfind('}') + 1]
    return text

class LangGraphHelper:
    def _thread_messages(self, thread):
        """
        Extract messages from the thread.
        """
        messages = []
        for email in thread.email_set.all():
            messages.append("From: %s <%s>: " % (email.sender.name, email.sender.email))
            messages.append("To: %s: " % email.to)
            messages.append("Date: %s: " % email.date)
            messages.append("Labels: %s: " % " ".join([l.name for l in email.labels.all()]))
            messages.append("Subject: %s: " % email.subject)
            messages.append(email.truncated_body)
            messages.append("----")
        return '\n'.join(messages)

    def create_thread_summary(self, thread):
        """
        Create a summary of the thread using LangGraph.
        """
        llm = OllamaLLM(model="gemma3:4b-it-qat")
        conversation = self._thread_messages(thread)
        participants = thread.participants

        prompt = PromptTemplate.from_template(PROMPT_SUMMARY)
        text = prompt.format(
            conversation = conversation,
            participants = '\n'.join([str(p) for p in participants])
        )
        print("Prompt: ", text)
        summary = llm.invoke(text)
        # Remove any character before the first '{' character and the last '}'
        summary = sanitize_json(summary)
        print("Summary: ", summary)
        # We will use the json module to decode the summary
        try:
            json_summary = json.loads(summary)
        except json.JSONDecodeError as e:
            print("Error decoding JSON: ", e)
            # If there is an error, we will return an empty summary
            json_summary = {
                "action": "IGNORE",
                "summary": summary,
                "participants": [],
                "rationale": ""
            }

        thread_summary = json_summary["summary"]

        participants_by_email = {p.email: p for p in participants}

        for participant in json_summary["participants"]:
            p = participants_by_email.get(participant["email"])

            print("Updating knowledge about ", p)
            
            if not p:
                print("Participant %s %s non identified by email" % (participant["name"], participant["email"]))
                continue

            # We want to update our knowledge of the participant based on what we have learnt
            prompt_text = PromptTemplate.from_template(
                PROMPT_PARTICIPANT_KNOWLEDGE
            )
            text = prompt_text.format(
                new_knowledge=participant["relevant information"],
                thread_summary=thread_summary,
                previous_knowledge=participants_by_email[p.email].knowledge

            )
            updated_knowledge_json = llm.invoke(text)
            updated_knowledge_json = sanitize_json(updated_knowledge_json)
            print("Updated knowledge :", updated_knowledge_json)
            updated_knowledge = json.loads(updated_knowledge_json)["updated_knowledge"]
            # We will update the knowledge of the participant in the database
            p.knowledge = updated_knowledge
            p.save()

        return json_summary

langgraph_helper = LangGraphHelper()
