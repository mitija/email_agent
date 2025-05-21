# -*- coding: utf-8 -*-
"""
This module contains utility functions for the LangGraph email processing system.
It provides LLM initialization and JSON handling utilities.
"""
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from core.llm.prompts import PROMPT_SUMMARY

# Initialize LLM instances
llm = OllamaLLM(model="gemma3:4b-it-qat")
summary_prompt = PromptTemplate(
    input_variables=["conversation", "participants"],
    template=PROMPT_SUMMARY
)
summary_chain = summary_prompt | llm

def sanitize_json(text):
    """
    Extract JSON from the text.
    This function will remove any character before the first '{' character and the last '}'
    """
    # Remove any character before the first '{' character and the last '}'
    text = text[text.find('{'):]
    text = text[:text.rfind('}') + 1]
    return text 