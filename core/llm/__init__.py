# -*- coding: utf-8 -*-
"""
LangGraph submodule for email processing.
This module provides a complete pipeline for analyzing, summarizing, and extracting knowledge from email threads.
"""
# Use lazy loading pattern to avoid immediate imports
from core.llm.helper import get_langgraph_helper 