# -*- coding: utf-8 -*-
"""
This module contains LangGraph node functions for the email processing system.
Each function represents a step in the LangGraph processing pipeline.
"""
import json
import sys
from string import Template
from langchain.prompts import PromptTemplate
from core.llm.types import ParticipantSet
from core.llm.prompts import PROMPT_PARTICIPANT_KNOWLEDGE, EMAIL_TEMPLATE, HEADER_TEMPLATE, PROMPT_SUMMARY
# Import models lazily to prevent AppRegistryNotReady errors
from django.apps import apps

def get_thread_summary_model():
    """Get the ThreadSummary model lazily"""
    return apps.get_model('core', 'ThreadSummary')

def get_llm_utils():
    """Get LLM utilities lazily to avoid circular imports"""
    from core.utils import sanitize_json, llm, summary_chain, log_llm_prompt
    return sanitize_json, llm, summary_chain, log_llm_prompt

def extract_thread_node(state):
    """Extract thread information and format messages"""
    thread = state["thread"]
    messages = []
    message_headers = []
    
    for email in thread.email_set.all():
        # Common data to extract
        values = {
            "sender": email.sender_str.original_string,
            "to_recipients": ", ".join([t.original_string for t in email.to_str.all()]),
            "cc_recipients": ", ".join([t.original_string for t in email.cc_str.all()]),
            "date": email.date,
            "labels": " ".join([l.name for l in email.labels.all()]),
            "subject": email.subject,
            "content": email.truncated_body,
            "snippet": email.snippet,
        }

        message = EMAIL_TEMPLATE.format(**values)
        header = HEADER_TEMPLATE.format(**values)
        messages.append(message)
        message_headers.append(header)
        
    return {
        "conversation": "\n".join(messages), 
        "message_headers": "\n".join(message_headers),
        **state
    }

def gather_knowledge_node(state):
    """Gather knowledge about participants"""
    thread = state["thread"]
    participant_set = ParticipantSet()

    for p in thread.participants:
        participant_set.add_email_str(p)

    return {
        **state, 
        "knowledge": str(participant_set), 
        "participant_set": participant_set
    }

def summarize_thread_node(state):
    """Generate summary for the thread"""
    sanitize_json, llm, summary_chain, log_llm_prompt = get_llm_utils()
    
    prompt_input = {
        "conversation": state["conversation"],
        "participants": state["knowledge"],
    }
    
    # Log the prompt before invoking
    log_llm_prompt(
        prompt_name="thread_summary",
        prompt_input=prompt_input,
        prompt_template=PROMPT_SUMMARY
    )
    
    result = summary_chain.invoke(prompt_input)
    
    try:
        summary_data = json.loads(sanitize_json(result))
    except json.JSONDecodeError:
        print("ERROR in decoding JSON")
        print(sanitize_json(result))
        summary_data = {
            "action": "IGNORE", 
            "summary": result, 
            "participants": [], 
            "rationale": ""
        }

    # Create and save thread summary - use lazy loading for model
    ThreadSummary = get_thread_summary_model()
    thread = state["thread"]
    thread_summary = ThreadSummary.objects.create(
        thread=thread,
        email=thread.email_set.last(),
        summary=summary_data["summary"],
        action=summary_data["action"],
        rationale=summary_data["rationale"],
        participants=summary_data["participants"]
    )  
    thread_summary.save()
    
    return {**state, "thread_summary": summary_data}

def update_knowledge_node(state):
    """Update knowledge about participants based on the summary"""
    thread = state["thread"]
    participants = state["thread_summary"]["participants"]
    print(state["thread_summary"])
    print(participants)
    thread_participants = thread.participants
    print("participants", thread_participants)
    participants_by_email = { tp.email: tp for tp in thread_participants }
    participants_by_name = { tp.name: tp for tp in thread_participants }
    thread_email_count = { tp.email: 0 for tp in thread_participants }
    for tp in thread_participants:
        thread_email_count[tp.email] += 1

    for participant in participants:
        # First we search by id
        id = None
        if type(participant["id"]) == int:
            id = participant["id"]
        elif type(participant["id"]) == str and participant["id"].isdigit():
            id = int(participant["id"])

        contact = None
        for tp in thread_participants:
            if tp.contact.id == id:
                contact = tp.contact
                break

        # If not found by ID then we search by name
        if contact == None:
            print("Searching for participant with name [%s]" %  participant["name"])
            print(participants_by_name)
            tp = participants_by_name.get(participant["name"])
            contact = tp.contact if tp else None

        # If not found by name then we search by email
        if contact == None:
            if thread_email_count.get(participant["email"]) != 1:
                print(f"Either no match of more than one match for {participant}")
                continue
            else:
                contact = participants_by_email.get(participant["email"])

        if contact == None:
            print(f"unable to find a match for {participant}")
            continue

        contact.knowledge = participant.get("updated_knowledge")
        contact.save()

    return state["thread_summary"] 
