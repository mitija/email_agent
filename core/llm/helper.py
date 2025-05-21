# -*- coding: utf-8 -*-
"""
This module provides the main LangGraph helper class for email processing.
It defines the graph structure and provides access to the compiled graph.
"""
from langgraph.graph import StateGraph, START, END
from core.llm.types import EmailThreadState
from core.llm.nodes import (
    extract_thread_node,
    gather_knowledge_node,
    summarize_thread_node,
    update_knowledge_node
)

def build_graph():
    """Build and compile the LangGraph for email processing"""
    builder = StateGraph(EmailThreadState)
    
    # Add nodes - each representing a step in the email processing pipeline
    builder.add_node("extract_thread", extract_thread_node)
    builder.add_node("gather_knowledge", gather_knowledge_node)
    builder.add_node("summarize_thread", summarize_thread_node)
    builder.add_node("update_knowledge", update_knowledge_node)
    
    # Define the flow of the graph
    builder.add_edge(START, "extract_thread")
    builder.add_edge("extract_thread", "gather_knowledge")
    builder.add_edge("gather_knowledge", "summarize_thread")
    builder.add_edge("summarize_thread", "update_knowledge")
    builder.add_edge("update_knowledge", END)
    
    return builder.compile()

# Use lazy loading pattern instead of immediate instantiation
_langgraph_helper = None

def get_langgraph_helper():
    """Get or create the langgraph helper instance"""
    global _langgraph_helper
    if _langgraph_helper is None:
        _langgraph_helper = build_graph()
    return _langgraph_helper 