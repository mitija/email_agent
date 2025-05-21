# -*- coding: utf-8 -*-
"""
This module contains node functions used by the LangGraph email processing system.
"""
import json
from langchain.prompts import PromptTemplate
from core.llm.types import ParticipantSet
from core.llm.utils import sanitize_json, llm, summary_chain
from core.llm.prompts import PROMPT_PARTICIPANT_KNOWLEDGE
# Import models lazily to prevent AppRegistryNotReady errors
from django.apps import apps

def get_thread_summary_model():
    """Get the ThreadSummary model lazily"""
    return apps.get_model('core', 'ThreadSummary')

def extract_thread_node(state):
    """Extract thread information and format messages"""
    thread = state["thread"]
    messages = []
    message_headers = []
    
    for email in thread.email_set.all():
        # Common data to extract
        sender = email.sender_str.original_string
        to_recipients = ", ".join([t.original_string for t in email.to_str.all()])
        cc_recipients = ", ".join([t.original_string for t in email.cc_str.all()])
        labels = " ".join([l.name for l in email.labels.all()])
        
        # Add to full messages
        messages.extend([
            f"From: {sender}",
            f"To: {to_recipients}",
            f"CC: {cc_recipients}",
            f"Date: {email.date}",
            f"Labels: {labels}",
            f"Subject: {email.subject}",
            email.truncated_body,
            "--"
        ])
        
        # Add to message headers
        message_headers.extend([
            f"From: {sender}",
            f"To: {to_recipients}",
            f"CC: {cc_recipients}",
            f"Date: {email.date}",
            f"Labels: {labels}",
            f"Subject: {email.subject}",
            "--"
        ])
        
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
    prompt_input = {
        "conversation": state["conversation"],
        "participants": state["knowledge"],
    }
    
    result = summary_chain.invoke(prompt_input)
    
    try:
        summary_data = json.loads(sanitize_json(result))
    except json.JSONDecodeError:
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
        summary=summary_data["summary"]
    )  
    thread_summary.save()
    
    return {**state, "thread_summary": summary_data}

def update_knowledge_node(state):
    """Update knowledge about participants based on the summary"""
    thread = state["thread"]
    thread_summary = state["thread_summary"]
    participant_set = state["participant_set"]
    participants_information = thread_summary["participants"]

    for p in participant_set.contacts:
        prompt_text = PromptTemplate.from_template(PROMPT_PARTICIPANT_KNOWLEDGE)
        text = prompt_text.format(
            thread_subject=thread.subject,
            message_headers=state["message_headers"],
            thread_summary=thread_summary["summary"],
            participants_information=participants_information,
            contact_name=p.name,
            previous_knowledge=p.knowledge
        )
        
        updated_knowledge_json = llm.invoke(text)
        updated_knowledge_json = sanitize_json(updated_knowledge_json)
        
        try:
            updated_knowledge = json.loads(updated_knowledge_json)["updated_knowledge"]
            p.knowledge = updated_knowledge
            p.save()
        except json.JSONDecodeError:
            continue
            
    return state["thread_summary"] 