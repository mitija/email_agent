# -*- coding: utf-8 -*-
"""
This module provides a helper class for LangGraph, which is used to create summaries of email threads.
and other things
"""
from django.db.models.query import EmptyQuerySet
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, START, END
import json
from typing import Any, List, Set, Dict
from typing_extensions import TypedDict
from core.models import Contact, ThreadSummary

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
          "email": "email address if known or N/A",
          "relevant information": "relevant information about this person gained from the thread" 
      }},
  ],
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

KNOWLEDGE_TEMPLATE = """
Contact Internal ID: %s
Name: %s
Appears as: %s
Existig knowedge: %s
"""

llm = OllamaLLM(model="gemma3:4b-it-qat")

summary_prompt = PromptTemplate(
    input_variables = [ "conversation", "participants"],
    template = PROMPT_SUMMARY
)

summary_chain = summary_prompt | OllamaLLM(model="gemma3:4b-it-qat")

def sanitize_json(text):
    """
    Extract JSON from the text.
    This function will remove any character before the first '{' character and the last '}'
    """
    # Remove any character before the first '{' character and the last '}'
    text = text[text.find('{'):]
    text = text[:text.rfind('}') + 1]
    return text

def extract_thread_node(state):
    print("DEBUG: extract_thread_node")
    print(state)
    thread = state["thread"]
    messages = []
    for email in thread.email_set.all():
        messages.append("From: %s: " % (email.sender_str.original_string))
        messages.append("To: %s: " % ", ".join([t.original_string for t in email.to_str.all()]))
        messages.append("CC: %s: " % ", ".join([t.original_string for t in email.cc_str.all()]))
        messages.append("Date: %s: " % email.date)
        messages.append("Labels: %s: " % " ".join([l.name for l in email.labels.all()]))
        messages.append("Subject: %s: " % email.subject)
        messages.append(email.truncated_body)
        messages.append("----")
    return {**state, "conversation": '\n'.join(messages)}

class ParticipantSet():
    contacts : Set
    email_str_list: Dict

    def __init__(self):
        self.email_str_list = dict()
        self.contacts = set()

    def add_email_str(self, email_str):
        contact = email_str.contact
        self.contacts.add(contact)
        email_strs = self.email_str_list.get(contact.id, [])
        email_strs.append(email_str.original_string)
        self.email_str_list[contact.id] = email_strs

    def __str__(self):
        result = ""
        for p in self.contacts:
            r = KNOWLEDGE_TEMPLATE % (p.id, p.name, self.email_str_list[p.id], p.knowledge)
            result += r 
        return result

def gather_knowledge_node(state):
    print("DEBUG: gather_knowledge_node")
    print(state)
    thread = state["thread"]
    participant_set = ParticipantSet()

    for p in thread.participants:
        participant_set.add_email_str(p)

    return { **state, "knowledge": str(participant_set) }

def summarize_thread_node(state):
    print("DEBUG: summarize_thread_node")
    print(state)
    prompt_input = {
            "conversation": state["conversation"],
            "participants": state["thread"].participants,
    }
    #replace the next line
    result = summary_chain.invoke(prompt_input)
    try:
        summary_data = json.loads(sanitize_json(result))
    except json.JSONDecodeError:
        summary_data = { "action": "IGNORE", "summary": result, "participants": [], "rationale": "" }

    # We create a new thread summary object
    # and we save it in the database
    thread = state["thread"]
    thread_summary = ThreadSummary.objects.create(
        thread=thread,
        email=thread.email_set.last(),
        summary=summary_data["summary"],
        #action=summary_data["action"],
        #rationale=summary_data["rationale"]
    )  
    thread_summary.save()
    return { **state, "thread_summary": summary_data }

def update_knowledge_node(state):
    print("DEBUG: update_knowledge_node")
    return state["thread_summary"]
    thread_summary = state["thread_summary"]
    participants = state["thread"].participants
    knowledge_by_email = state["knowledge"]
    participants_by_email = { p.email: p for p in participants if p.email }
 
    for participant in thread_summary["participants"]:
        p = participants_by_email.get(participant["email"])
        if not p:
            print("Participant %s %s non identified by email" % (participant["name"], participant["email"]))
            continue

        # We want to update our knowledge of the participant based on what we have learnt
        prompt_text = PromptTemplate.from_template(
            PROMPT_PARTICIPANT_KNOWLEDGE
        )
        text = prompt_text.format(
            new_knowledge=participant["relevant information"],
            thread_summary=state["thread_summary"]["summary"],
            previous_knowledge=knowledge_by_email[p.email]
        )
        updated_knowledge_json = llm.invoke(text)
        updated_knowledge_json = sanitize_json(updated_knowledge_json)
        try:
            updated_knowledge = json.loads(updated_knowledge_json)["updated_knowledge"]
        except json.JSONDecodeError:
            continue
        # We will update the knowledge of the participant in the database
        p.knowledge = updated_knowledge
        p.save()
    return state["thread_summary"]

class MySchema(TypedDict):
    thread_summary: Any
    thread: Any
    conversation: str
    participants: List[Any]
    knowledge: Any



builder = StateGraph(MySchema)
builder.add_node("extract_thread", extract_thread_node)
builder.add_node("gather_knowledge", gather_knowledge_node)
builder.add_node("summarize_thread", summarize_thread_node)
builder.add_node("update_knowledge", update_knowledge_node)

builder.add_edge(START, "extract_thread")
builder.add_edge("extract_thread", "gather_knowledge")
builder.add_edge("gather_knowledge", "summarize_thread")
builder.add_edge("summarize_thread", "update_knowledge")
builder.add_edge("update_knowledge", END)

langgraph_helper = builder.compile()

