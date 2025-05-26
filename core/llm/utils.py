# -*- coding: utf-8 -*-
"""
This module contains utility functions for the LangGraph email processing system.
It provides LLM initialization and JSON handling utilities.
"""
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from core.llm.prompts import PROMPT_SUMMARY
import json
import logging
from datetime import datetime
import codecs

# Initialize LLM instances
llm = OllamaLLM(model="gemma3:12b-it-qat")
summary_prompt = PromptTemplate(
    input_variables=["conversation", "participants"],
    template=PROMPT_SUMMARY
)
summary_chain = summary_prompt | llm

# Configure logging with UTF-8 encoding
logging.basicConfig(
    filename='llm_prompts.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    encoding='utf-8'  # Explicitly set UTF-8 encoding
)

def log_llm_prompt(prompt_name, prompt_input, prompt_template=None):
    """
    Log LLM prompts to a file with timestamp and context.
    
    Args:
        prompt_name (str): Name/identifier of the prompt
        prompt_input (dict): Input variables for the prompt
        prompt_template (str, optional): The prompt template being used
    """
    # Format the prompt with variables if template is provided
    formatted_prompt = None
    if prompt_template:
        try:
            # Create a temporary PromptTemplate to format the prompt
            temp_prompt = PromptTemplate(
                template=prompt_template,
                input_variables=list(prompt_input.keys())
            )
            formatted_prompt = temp_prompt.format(**prompt_input)
        except Exception as e:
            formatted_prompt = f"Error formatting prompt: {str(e)}"
    
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'prompt_name': prompt_name,
        'prompt_input': prompt_input,
        'prompt_template': prompt_template,
        'formatted_prompt': formatted_prompt
    }
    
    # Write directly to file with proper formatting
    with codecs.open('llm_prompts.log', 'a', encoding='utf-8') as f:
        f.write(f"=== {log_entry['timestamp']} - {log_entry['prompt_name']} ===\n")
        f.write("Input Variables:\n")
        f.write(json.dumps(log_entry['prompt_input'], ensure_ascii=False, indent=2))
        f.write("\n\nTemplate:\n")
        f.write(log_entry['prompt_template'] or "None")
        f.write("\n\nFormatted Prompt:\n")
        f.write(log_entry['formatted_prompt'] or "None")
        f.write("\n\n" + "="*50 + "\n\n")

def sanitize_json(text):
    """
    Extract JSON from the text.
    This function will remove any character before the first '{' character and the last '}'
    """
    # Remove any character before the first '{' character and the last '}'
    text = text[text.find('{'):]
    text = text[:text.rfind('}') + 1]
    return text 
