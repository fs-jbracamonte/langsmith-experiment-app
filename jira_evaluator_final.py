#!/usr/bin/env python3
"""
JIRA Truthfulness Evaluator for LangSmith

Evaluates whether AI-generated reports contain only truthful JIRA ticket references
by comparing output references against input ground truth tickets.

This evaluator handles both XML formatted JIRA data (RSS format) and plain text formats,
automatically detecting the format and applying the appropriate parsing method.

USAGE IN LANGSMITH:
==================

1. Simple Evaluation (Binary Score):
   - Use: perform_eval(run, example)
   - Returns: {"truthfulness": 1 or 0}

2. Detailed Evaluation (With Metadata):
   - Use: perform_detailed_eval(run, example)
   - Returns: Comprehensive metrics including counts, accuracy, format detection, etc.

EXPECTED INPUT FORMAT:
=====================
- Input should contain JIRA tickets between <<START OF JIRA TICKETS>> and <<END OF JIRA TICKETS>> delimiters (XML format)
- OR JIRA tickets in plain text anywhere in the input (fallback mode)
- XML format: RSS feed with <item><title>[TICKET-123] Description</title></item> structure

DEPLOYMENT NOTES:
================
- Both evaluators are production-ready and handle various LangSmith object structures
- XML parsing with automatic fallback to regex ensures compatibility with all data formats
- Conservative error handling: returns 0 (untruthful) on any parsing errors
"""

import json
import re
import xml.etree.ElementTree as ET
from typing import Optional, List, Tuple


def extract_jira_data_from_input(content: str) -> Tuple[Optional[str], bool]:
    """
    Extract raw JIRA data from content between delimiters or return entire content.
    
    Args:
        content: Raw input content that may contain JIRA ticket data
        
    Returns:
        tuple: (raw_data, has_delimiters)
            - raw_data: Raw JIRA text between delimiters or entire content
            - has_delimiters: True if delimiters were found, False otherwise
    """
    if not content:
        return None, False
    
    start_delimiter = "<<START OF JIRA TICKETS>>"
    end_delimiter = "<<END OF JIRA TICKETS>>"
    
    start_index = content.find(start_delimiter)
    end_index = content.find(end_delimiter)
    
    # Check if both delimiters are present
    if start_index != -1 and end_index != -1:
        # Extract the raw JIRA data between delimiters
        start_index += len(start_delimiter)
        
        if start_index >= end_index:
            return None, False
        
        jira_raw_data = content[start_index:end_index].strip()
        
        if not jira_raw_data:
            return None, False
        
        return jira_raw_data, True
    else:
        # Delimiters not found - use entire content as fallback
        return content.strip(), False


def extract_jira_ticket_numbers(jira_raw_data: str, has_delimiters: bool = True) -> List[str]:
    """
    Extract JIRA ticket numbers from raw JIRA data.
    
    This function handles both XML formatted JIRA data (RSS format) and plain text.
    If delimiters were found, it tries XML parsing first, then falls back to regex.
    If no delimiters were found, it skips XML parsing and goes directly to regex.
    
    Args:
        jira_raw_data: Raw JIRA data containing ticket information
        has_delimiters: Whether delimiters were found in the input (True = try XML first, False = regex only)
    
    Returns:
        List[str]: List of unique JIRA ticket numbers found
    """
    if not jira_raw_data:
        return []
    
    try:
        # If delimiters were found, try XML parsing first
        if has_delimiters:
            try:
                # Parse the XML data
                root = ET.fromstring(jira_raw_data)
                
                # Find all <item> elements (JIRA tickets)
                items = root.findall('.//item')
                
                unique_tickets = []
                seen = set()
                
                for item in items:
                    # Get the title element
                    title_element = item.find('title')
                    if title_element is not None and title_element.text:
                        title_text = title_element.text
                        
                        # Extract ticket number from title
                        # Pattern: [TICKET-123] Description
                        ticket_match = re.search(r'\[([A-Z]{2,10}-\d{1,6})\]', title_text)
                        if ticket_match:
                            ticket_number = ticket_match.group(1)
                            if ticket_number not in seen:
                                unique_tickets.append(ticket_number)
                                seen.add(ticket_number)
                
                return unique_tickets
                
            except ET.ParseError:
                # XML parsing failed, fall back to regex
                pass
        
        # Use regex pattern matching for plain text format
        # (either as fallback from failed XML parsing, or primary method when no delimiters)
        ticket_pattern = r'\b[A-Z]{2,10}-\d{1,6}\b'
        matches = re.findall(ticket_pattern, jira_raw_data)
        
        # Remove duplicates while preserving order
        unique_tickets = []
        seen = set()
        for ticket in matches:
            if ticket not in seen:
                unique_tickets.append(ticket)
                seen.add(ticket)
        
        return unique_tickets
        
    except Exception:
        return []


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
    
    This function compares JIRA tickets mentioned in AI output against
    the actual JIRA tickets available in the input data, supporting both
    XML (RSS) format and plain text format JIRA data.
    
    Args:
        run: Run object containing AI output
        example: Example object containing input data with JIRA tickets
    
    Returns:
        dict: {"truthfulness": score} where score is 1 (truthful) or 0 (untruthful)
    """
    try:
        # Extract JIRA tickets from input data (ground truth)
        input_content = ""
        
        # Handle different input structures
        if ("inputs" in example and 
            "messages" in example["inputs"] and 
            len(example["inputs"]["messages"]) > 0 and
            "content" in example["inputs"]["messages"][0]):
            input_content = example["inputs"]["messages"][0]["content"]
        elif "inputs" in example and isinstance(example["inputs"], str):
            input_content = example["inputs"]
        elif hasattr(example, 'inputs') and hasattr(example.inputs, 'get'):
            # Handle LangSmith Example object
            messages = example.inputs.get("messages", [])
            if messages and len(messages) > 0 and "content" in messages[0]:
                input_content = messages[0]["content"]
        
        # Extract JIRA data with new improved function
        jira_raw_data, has_delimiters = extract_jira_data_from_input(input_content)
        input_tickets = extract_jira_ticket_numbers(jira_raw_data, has_delimiters) if jira_raw_data else []
        
        # Extract JIRA references from AI output
        output_content = ""
        
        # Handle different output structures
        if ("outputs" in run and 
            "message" in run["outputs"] and 
            "content" in run["outputs"]["message"]):
            output_content = run["outputs"]["message"]["content"]
        elif "outputs" in run and "output" in run["outputs"]:
            output_content = str(run["outputs"]["output"])
        elif hasattr(run, 'outputs') and hasattr(run.outputs, 'get'):
            # Handle LangSmith Run object
            if "content" in run.outputs:
                output_content = run.outputs["content"]
            elif "message" in run.outputs:
                output_content = str(run.outputs["message"])
            else:
                output_content = str(run.outputs)
        
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


def perform_detailed_eval(run, example):
    """
    Evaluate the truthfulness of JIRA ticket references with detailed metadata.
    
    This comprehensive evaluator provides additional metrics and debugging information
    useful for analysis and monitoring in LangSmith.
    
    Args:
        run: Run object containing AI output
        example: Example object containing input data with JIRA tickets
    
    Returns:
        dict: Detailed evaluation results including truthfulness score and metadata
    """
    try:
        # Extract JIRA tickets from input data (ground truth)
        input_content = ""
        
        # Handle different input structures
        if ("inputs" in example and 
            "messages" in example["inputs"] and 
            len(example["inputs"]["messages"]) > 0 and
            "content" in example["inputs"]["messages"][0]):
            input_content = example["inputs"]["messages"][0]["content"]
        elif "inputs" in example and isinstance(example["inputs"], str):
            input_content = example["inputs"]
        elif hasattr(example, 'inputs') and hasattr(example.inputs, 'get'):
            # Handle LangSmith Example object
            messages = example.inputs.get("messages", [])
            if messages and len(messages) > 0 and "content" in messages[0]:
                input_content = messages[0]["content"]
        
        # Extract JIRA data with metadata
        jira_raw_data, has_delimiters = extract_jira_data_from_input(input_content)
        input_tickets = extract_jira_ticket_numbers(jira_raw_data, has_delimiters) if jira_raw_data else []
        
        # Extract JIRA references from AI output
        output_content = ""
        
        # Handle different output structures
        if ("outputs" in run and 
            "message" in run["outputs"] and 
            "content" in run["outputs"]["message"]):
            output_content = run["outputs"]["message"]["content"]
        elif "outputs" in run and "output" in run["outputs"]:
            output_content = str(run["outputs"]["output"])
        elif hasattr(run, 'outputs') and hasattr(run.outputs, 'get'):
            # Handle LangSmith Run object
            if "content" in run.outputs:
                output_content = run.outputs["content"]
            elif "message" in run.outputs:
                output_content = str(run.outputs["message"])
            else:
                output_content = str(run.outputs)
        
        output_references = extract_jira_references_from_output(output_content)
        
        # Calculate detailed metrics
        input_set = set(input_tickets)
        output_set = set(output_references)
        
        valid_references = output_set.intersection(input_set)
        invalid_references = output_set - input_set
        unreferenced_tickets = input_set - output_set
        
        # Determine final truthfulness score
        truthfulness_score = 1 if len(invalid_references) == 0 else 0
        
        # Handle edge case: no output references
        if not output_references:
            truthfulness_score = 1  # No references is considered truthful
        
        # Handle edge case: no input tickets but AI made references
        if not input_tickets and output_references:
            truthfulness_score = 0  # Unverifiable references are untruthful
        
        # Calculate accuracy rate
        accuracy_rate = 0.0
        if len(output_references) > 0:
            accuracy_rate = len(valid_references) / len(output_references)
        
        return {
            "truthfulness": truthfulness_score,
            "input_ticket_count": len(input_tickets),
            "output_reference_count": len(output_references),
            "valid_reference_count": len(valid_references),
            "invalid_reference_count": len(invalid_references),
            "unreferenced_ticket_count": len(unreferenced_tickets),
            "accuracy_rate": accuracy_rate,
            "has_delimiters": has_delimiters,
            "format_detected": "xml" if has_delimiters else "text",
            "invalid_references": list(invalid_references)[:5],  # Limit to 5 for brevity
            "valid_references": list(valid_references)[:5]  # Limit to 5 for brevity
        }
        
    except Exception as e:
        # In case of error, return detailed error info
        return {
            "truthfulness": 0,
            "error": str(e),
            "input_ticket_count": 0,
            "output_reference_count": 0,
            "valid_reference_count": 0,
            "invalid_reference_count": 0,
            "accuracy_rate": 0.0,
            "has_delimiters": False,
            "format_detected": "error"
        }


# For backward compatibility and simple use cases
evaluate_jira_truthfulness = perform_eval 