# -*- coding: utf-8 -*-
"""
This module provides a helper class for LangGraph, which is used to create summaries of email threads.
and other things
"""
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
        messages.append("--")

    message_headers = []
    for email in thread.email_set.all():
        message_headers.append("From: %s: " % (email.sender_str.original_string))
        message_headers.append("To: %s: " % ", ".join([t.original_string for t in email.to_str.all()]))
        message_headers.append("CC: %s: " % ", ".join([t.original_string for t in email.cc_str.all()]))
        message_headers.append("Date: %s: " % email.date)
        message_headers.append("Labels: %s: " % " ".join([l.name for l in email.labels.all()]))
        message_headers.append("Subject: %s: " % email.subject)
        message_headers.append("--")
    return {"conversation": "\n".join(messages), "message_headers": "\n".join(message_headers), **state}

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

    return { **state, "knowledge": str(participant_set), "participant_set": participant_set }

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
    print("DDDDDDDDDDDDDDDDDDDDDDDDDDDD")
    print("DEBUG: update_knowledge_node")
    thread = state["thread"]
    thread_summary = state["thread_summary"]
    message_headers = state["message_headers"]
    participants_information = thread_summary["participants"]

    participant_set = state["participant_set"]

    for p in participant_set.contacts:
        # We want to update our knowledge of the participant based on what we have learnt
        prompt_text = PromptTemplate.from_template(
            PROMPT_PARTICIPANT_KNOWLEDGE
        )
        text = prompt_text.format(
            thread_subject = thread.subject,
            message_headers = state["message_headers"],
            thread_summary= thread_summary["summary"],
            participants_information = participants_information,
            contact_name = p.name,
            previous_knowledge=p.knowledge
        )
        updated_knowledge_json = llm.invoke(text)
        updated_knowledge_json = sanitize_json(updated_knowledge_json)
        try:
            updated_knowledge = json.loads(updated_knowledge_json)["updated_knowledge"]
            print(">>>>>> Updating knowledge for", p.name, " new knowledge:", updated_knowledge)
            # We will update the knowledge of the participant in the database
            p.knowledge = updated_knowledge
            p.save()
        except json.JSONDecodeError:
            print(">>>>> Error in decoding json", updated_knowledge)
            continue
    return state["thread_summary"]

class MySchema(TypedDict):
    conversation: str
    message_headers: str
    thread_summary: Any
    thread: Any
    participants: List[Any]
    knowledge: Any
    participant_set: ParticipantSet



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

