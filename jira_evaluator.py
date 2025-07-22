#!/usr/bin/env python3
"""
JIRA Evaluator Functions

Functions for extracting and validating JIRA ticket references 
from LangSmith dataset rows to evaluate AI report truthfulness.
"""

import json
import re
from typing import Optional, Dict, Any, List


def extract_jira_data_from_input(dataset_row: Dict[str, Any]) -> Optional[str]:
    """
    Extract raw JIRA data from a dataset row's inputs_json.
    
    This function looks for JIRA ticket data between the delimiters:
    <<START OF JIRA TICKETS>> and <<END OF JIRA TICKETS>>
    
    Args:
        dataset_row: A single row from the LangSmith dataset containing
                    'inputs_json' field with the raw JSON string
    
    Returns:
        str: Raw JIRA text between delimiters, or None if not found
        
    Raises:
        ValueError: If inputs_json is malformed or missing required fields
    """
    try:
        # Parse the inputs_json string into a Python dictionary
        inputs_data = json.loads(dataset_row['inputs_json'])
        
        # Navigate to the content field within the JSON structure
        # Based on the sample data: inputs_json -> messages -> [0] -> content
        if 'messages' not in inputs_data:
            raise ValueError("No 'messages' field found in inputs_json")
        
        if not inputs_data['messages'] or len(inputs_data['messages']) == 0:
            raise ValueError("Messages array is empty in inputs_json")
        
        # Get the content from the first message (system message typically contains the data)
        content = inputs_data['messages'][0].get('content', '')
        
        if not content:
            raise ValueError("No 'content' field found in first message")
        
        # Look for JIRA delimiters
        start_delimiter = "<<START OF JIRA TICKETS>>"
        end_delimiter = "<<END OF JIRA TICKETS>>"
        
        start_index = content.find(start_delimiter)
        if start_index == -1:
            print("Warning: START OF JIRA TICKETS delimiter not found")
            return None
        
        end_index = content.find(end_delimiter)
        if end_index == -1:
            print("Warning: END OF JIRA TICKETS delimiter not found")
            return None
        
        # Extract the raw JIRA data between delimiters
        # Move start_index past the delimiter
        start_index += len(start_delimiter)
        
        if start_index >= end_index:
            print("Warning: Invalid delimiter positions - start after end")
            return None
        
        jira_raw_data = content[start_index:end_index].strip()
        
        if not jira_raw_data:
            print("Warning: No JIRA data found between delimiters")
            return None
        
        print(f"✅ Successfully extracted JIRA data ({len(jira_raw_data)} characters)")
        return jira_raw_data
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse inputs_json: {e}")
    except KeyError as e:
        raise ValueError(f"Missing required field in dataset row: {e}")
    except Exception as e:
        raise ValueError(f"Unexpected error extracting JIRA data: {e}")


def extract_jira_ticket_numbers(jira_raw_data: str) -> List[str]:
    """
    Extract JIRA ticket numbers from raw JIRA data.
    
    This function looks for ticket number patterns like:
    - BUG-123
    - FEAT-456  
    - PROJ-789
    - ABC-1234
    
    Args:
        jira_raw_data: Raw JIRA text containing ticket information
    
    Returns:
        List[str]: List of unique JIRA ticket numbers found
    """
    if not jira_raw_data:
        print("Warning: No JIRA data provided")
        return []
    
    try:
        # Regex pattern to match JIRA ticket numbers
        # Matches: [2-10 uppercase letters]-[1-6 digits]
        # Examples: BUG-123, FEATURE-4567, PROJ-1, ABC-999999
        ticket_pattern = r'\b[A-Z]{2,10}-\d{1,6}\b'
        
        # Find all matches
        matches = re.findall(ticket_pattern, jira_raw_data)
        
        # Remove duplicates while preserving order
        unique_tickets = []
        seen = set()
        for ticket in matches:
            if ticket not in seen:
                unique_tickets.append(ticket)
                seen.add(ticket)
        
        print(f"✅ Found {len(unique_tickets)} unique JIRA ticket numbers")
        if unique_tickets:
            print(f"📋 Sample tickets: {unique_tickets[:5]}{'...' if len(unique_tickets) > 5 else ''}")
        
        return unique_tickets
        
    except Exception as e:
        print(f"❌ Error extracting ticket numbers: {e}")
        return []


def extract_jira_references_from_output(dataset_row: Dict[str, Any]) -> List[str]:
    """
    Extract JIRA ticket references from a dataset row's outputs_json.
    
    This function searches for JIRA ticket references that the AI mentions
    in its generated report/response.
    
    Args:
        dataset_row: A single row from the LangSmith dataset containing
                    'outputs_json' field with the AI-generated response
    
    Returns:
        List[str]: List of unique JIRA ticket numbers referenced in the output
    """
    try:
        # Parse the outputs_json string into a Python dictionary
        outputs_data = json.loads(dataset_row['outputs_json'])
        
        # Extract text content from outputs - handle different possible structures
        output_text = ""
        
        # Common output structures to check:
        if isinstance(outputs_data, dict):
            # Check common field names for AI responses
            possible_fields = ['content', 'response', 'answer', 'result', 'output', 'text', 'message']
            
            for field in possible_fields:
                if field in outputs_data:
                    if isinstance(outputs_data[field], str):
                        output_text = outputs_data[field]
                        break
                    elif isinstance(outputs_data[field], dict):
                        # Sometimes content is nested, like {'content': {'text': '...'}}
                        if 'text' in outputs_data[field]:
                            output_text = outputs_data[field]['text']
                            break
            
            # If no common field found, convert entire dict to string as fallback
            if not output_text:
                output_text = str(outputs_data)
                
        elif isinstance(outputs_data, str):
            # Sometimes outputs_json is just a plain string
            output_text = outputs_data
        else:
            # Fallback: convert to string
            output_text = str(outputs_data)
        
        if not output_text:
            print("Warning: No output text found to search for JIRA references")
            return []
        
        print(f"📝 Searching for JIRA references in output ({len(output_text)} characters)")
        
        # Use the same regex pattern as extract_jira_ticket_numbers
        ticket_pattern = r'\b[A-Z]{2,10}-\d{1,6}\b'
        
        # Find all JIRA ticket references in the output
        matches = re.findall(ticket_pattern, output_text)
        
        # Remove duplicates while preserving order
        unique_references = []
        seen = set()
        for ticket in matches:
            if ticket not in seen:
                unique_references.append(ticket)
                seen.add(ticket)
        
        print(f"🎫 Found {len(unique_references)} unique JIRA ticket references in output")
        if unique_references:
            print(f"📋 References found: {unique_references[:10]}{'...' if len(unique_references) > 10 else ''}")
        
        return unique_references
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse outputs_json: {e}")
        return []
    except Exception as e:
        print(f"❌ Error extracting JIRA references from output: {e}")
        return []


def evaluate_jira_truthfulness(dataset_row: Dict[str, Any]) -> int:
    """
    Evaluate the truthfulness of JIRA ticket references in AI output.
    
    This function compares JIRA tickets mentioned in AI output against
    the actual JIRA tickets available in the input data.
    
    Args:
        dataset_row: A single row from the LangSmith dataset containing
                    both 'inputs_json' and 'outputs_json' fields
    
    Returns:
        int: 1 if all AI references are valid (truthful), 
             0 if any AI references are invalid (hallucinated)
    """
    try:
        print(f"🔍 Evaluating JIRA truthfulness for row: {dataset_row.get('id', 'unknown')}")
        
        # Step 1: Extract JIRA tickets from input data (ground truth)
        jira_raw_data = extract_jira_data_from_input(dataset_row)
        if jira_raw_data:
            input_tickets = extract_jira_ticket_numbers(jira_raw_data)
        else:
            input_tickets = []
        
        # Step 2: Extract JIRA references from AI output
        output_references = extract_jira_references_from_output(dataset_row)
        
        print(f"📥 Input tickets available: {len(input_tickets)}")
        print(f"📤 Output references made: {len(output_references)}")
        
        # Step 3: Handle edge cases
        if not output_references:
            # AI made no JIRA references - this is considered truthful
            print("✅ AI made no JIRA references - scoring as truthful (1)")
            return 1
        
        if not input_tickets:
            # No input JIRA data to verify against, but AI made references
            print("⚠️ No input JIRA data available, but AI made references - scoring as untruthful (0)")
            return 0
        
        # Step 4: Compare output references against input tickets
        input_set = set(input_tickets)
        output_set = set(output_references)
        
        # Find valid and invalid references
        valid_references = output_set.intersection(input_set)
        invalid_references = output_set - input_set
        
        print(f"✅ Valid references: {len(valid_references)}")
        print(f"❌ Invalid references: {len(invalid_references)}")
        
        if invalid_references:
            print(f"🚨 Hallucinated tickets detected: {list(invalid_references)}")
            print("📊 Truthfulness score: 0 (contains hallucinations)")
            return 0
        else:
            print(f"✓ All references are valid: {list(valid_references)}")
            print("📊 Truthfulness score: 1 (completely truthful)")
            return 1
            
    except Exception as e:
        print(f"❌ Error during truthfulness evaluation: {e}")
        # In case of error, default to untruthful to be conservative
        print("📊 Truthfulness score: 0 (error during evaluation)")
        return 0


def test_jira_extraction():
    """
    Test function to demonstrate JIRA data extraction with sample data.
    This helps verify the function works before integrating with real datasets.
    """
    # Sample dataset row structure (simplified for testing)
    sample_row = {
        'id': 'test-123',
        'inputs_json': json.dumps({
            'messages': [{
                'role': 'system',
                'content': '''
                Some content before...
                
                <<START OF JIRA TICKETS>>
                
                Summary | Issue key | Issue id | Issue Type | Status | Project key
                Fix login bug | BUG-123 | 12345 | Bug | Done | PROJ
                Add new feature | FEAT-456 | 67890 | Story | In Progress | PROJ
                
                <<END OF JIRA TICKETS>>
                
                Some content after...
                '''
            }]
        }),
        'outputs_json': '{"result": "Based on analysis of BUG-123 and FEAT-456, we found issues. The STORY-789 was completed successfully."}'
    }
    
    print("🧪 Testing JIRA extraction function...")
    print("-" * 50)
    
    try:
        jira_data = extract_jira_data_from_input(sample_row)
        
        if jira_data:
            print(f"📊 Extracted JIRA data:")
            print(f"📏 Length: {len(jira_data)} characters")
            print(f"📝 Preview:")
            print(jira_data[:200] + "..." if len(jira_data) > 200 else jira_data)
            
            # Test ticket number extraction from input
            print(f"\n🎫 Testing ticket number extraction from input...")
            ticket_numbers = extract_jira_ticket_numbers(jira_data)
            
            if ticket_numbers:
                print(f"📋 Extracted {len(ticket_numbers)} ticket numbers from input:")
                for i, ticket in enumerate(ticket_numbers, 1):
                    print(f"   {i}. {ticket}")
            else:
                print("❌ No ticket numbers found in input")
                
        else:
            print("❌ No JIRA data extracted from input")
        
        # Test JIRA reference extraction from output
        print(f"\n🎯 Testing JIRA reference extraction from output...")
        output_references = extract_jira_references_from_output(sample_row)
        
        if output_references:
            print(f"📋 Found {len(output_references)} JIRA references in output:")
            for i, ref in enumerate(output_references, 1):
                print(f"   {i}. {ref}")
        else:
            print("❌ No JIRA references found in output")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")


if __name__ == "__main__":
    # Run test when script is executed directly
    test_jira_extraction() 