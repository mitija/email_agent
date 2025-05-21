# -*- coding: utf-8 -*-
"""
This module contains type definitions and data classes used by the LangGraph email processing system.
"""
from typing import Any, List, Set, Dict
from typing_extensions import TypedDict
from core.llm.prompts import KNOWLEDGE_TEMPLATE

# Define the state schema
class EmailThreadState(TypedDict):
    conversation: str
    message_headers: str
    thread_summary: Any
    thread: Any
    participants: List[Any]
    knowledge: Any
    participant_set: Any

# Helper class for managing participants
class ParticipantSet:
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