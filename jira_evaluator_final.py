#!/usr/bin/env python3
"""
JIRA Truthfulness Evaluator for LangSmith

Evaluates whether AI-generated reports contain only truthful JIRA ticket references
by comparing output references against input ground truth tickets.
"""

import json
import re
from typing import Optional, List


def extract_jira_data_from_input(content: str) -> Optional[str]:
    """Extract raw JIRA data from content between delimiters."""
    start_delimiter = "<<START OF JIRA TICKETS>>"
    end_delimiter = "<<END OF JIRA TICKETS>>"
    
    start_index = content.find(start_delimiter)
    if start_index == -1:
        return None
    
    end_index = content.find(end_delimiter)
    if end_index == -1:
        return None
    
    # Extract the raw JIRA data between delimiters
    start_index += len(start_delimiter)
    if start_index >= end_index:
        return None
    
    jira_raw_data = content[start_index:end_index].strip()
    return jira_raw_data if jira_raw_data else None


def extract_jira_ticket_numbers(jira_raw_data: str) -> List[str]:
    """Extract JIRA ticket numbers from raw JIRA data."""
    if not jira_raw_data:
        return []
    
    # Regex pattern to match JIRA ticket numbers
    # Matches: [2-10 uppercase letters]-[1-6 digits]
    ticket_pattern = r'\b[A-Z]{2,10}-\d{1,6}\b'
    
    # Find all matches and remove duplicates while preserving order
    matches = re.findall(ticket_pattern, jira_raw_data)
    unique_tickets = []
    seen = set()
    for ticket in matches:
        if ticket not in seen:
            unique_tickets.append(ticket)
            seen.add(ticket)
    
    return unique_tickets


def extract_jira_references_from_output(output_content: str) -> List[str]:
    """Extract JIRA ticket references from AI output content."""
    if not output_content:
        return []
    
    # Use the same regex pattern as extract_jira_ticket_numbers
    ticket_pattern = r'\b[A-Z]{2,10}-\d{1,6}\b'
    
    # Find all JIRA ticket references in the output
    matches = re.findall(ticket_pattern, output_content)
    
    # Remove duplicates while preserving order
    unique_references = []
    seen = set()
    for ticket in matches:
        if ticket not in seen:
            unique_references.append(ticket)
            seen.add(ticket)
    
    return unique_references


def perform_eval(run, example):
    """
    Evaluate the truthfulness of JIRA ticket references in AI output.
    
    Args:
        run: Run object containing AI output
        example: Example object containing input data with JIRA tickets
    
    Returns:
        dict: {"truthfulness": score} where score is 1 (truthful) or 0 (untruthful)
    """
    try:
        # Extract JIRA tickets from input data (ground truth)
        input_content = ""
        if ("inputs" in example and 
            "messages" in example["inputs"] and 
            len(example["inputs"]["messages"]) > 0 and
            "content" in example["inputs"]["messages"][0]):
            input_content = example["inputs"]["messages"][0]["content"]
        
        jira_raw_data = extract_jira_data_from_input(input_content)
        input_tickets = extract_jira_ticket_numbers(jira_raw_data) if jira_raw_data else []
        
        # Extract JIRA references from AI output
        output_content = ""
        if ("outputs" in run and 
            "message" in run["outputs"] and 
            "content" in run["outputs"]["message"]):
            output_content = run["outputs"]["message"]["content"]
        elif "outputs" in run and "output" in run["outputs"]:
            output_content = str(run["outputs"]["output"])
        
        output_references = extract_jira_references_from_output(output_content)
        
        # Handle edge cases
        if not output_references:
            # AI made no JIRA references - this is considered truthful
            return {"truthfulness": 1}
        
        if not input_tickets:
            # No input JIRA data to verify against, but AI made references
            return {"truthfulness": 0}
        
        # Compare output references against input tickets
        input_set = set(input_tickets)
        output_set = set(output_references)
        
        # Find invalid references (hallucinations)
        invalid_references = output_set - input_set
        
        # Return 1 if all references are valid, 0 if any are invalid
        score = 1 if len(invalid_references) == 0 else 0
        return {"truthfulness": score}
        
    except Exception as e:
        # In case of error, default to untruthful to be conservative
        return {"truthfulness": 0} 