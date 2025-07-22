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
        'outputs_json': '{"result": "test output"}'
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
            
            # Test ticket number extraction
            print(f"\n🎫 Testing ticket number extraction...")
            ticket_numbers = extract_jira_ticket_numbers(jira_data)
            
            if ticket_numbers:
                print(f"📋 Extracted {len(ticket_numbers)} ticket numbers:")
                for i, ticket in enumerate(ticket_numbers, 1):
                    print(f"   {i}. {ticket}")
            else:
                print("❌ No ticket numbers found")
                
        else:
            print("❌ No JIRA data extracted")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")


if __name__ == "__main__":
    # Run test when script is executed directly
    test_jira_extraction() 