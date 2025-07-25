#!/usr/bin/env python3
"""
JIRA Evaluator Functions

Functions for extracting and validating JIRA ticket references 
from LangSmith dataset rows to evaluate AI report truthfulness.
"""

import json
import re
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List


def extract_jira_data_from_input(dataset_row: Dict[str, Any]) -> tuple[Optional[str], bool]:
    """
    Extract raw JIRA data from a dataset row's inputs_json.
    
    This function looks for JIRA ticket data between the delimiters:
    <<START OF JIRA TICKETS>> and <<END OF JIRA TICKETS>>
    If delimiters are not found, returns the entire content.
    
    Args:
        dataset_row: A single row from the LangSmith dataset containing
                    'inputs_json' field with the raw JSON string
    
    Returns:
        tuple: (raw_data, has_delimiters)
            - raw_data: Raw JIRA text between delimiters or entire content
            - has_delimiters: True if delimiters were found, False otherwise
        
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
        end_index = content.find(end_delimiter)
        
        # Check if both delimiters are present
        if start_index != -1 and end_index != -1:
            # Extract the raw JIRA data between delimiters
            # Move start_index past the delimiter
            start_index += len(start_delimiter)
            
            if start_index >= end_index:
                print("Warning: Invalid delimiter positions - start after end")
                return None, False
            
            jira_raw_data = content[start_index:end_index].strip()
            
            if not jira_raw_data:
                print("Warning: No JIRA data found between delimiters")
                return None, False
            
            print(f"✅ Successfully extracted JIRA data from delimiters ({len(jira_raw_data)} characters)")
            return jira_raw_data, True
        
        else:
            # Delimiters not found - use entire content as fallback
            print("ℹ️ JIRA delimiters not found - searching entire input content for JIRA tickets")
            print(f"✅ Using entire input content ({len(content)} characters)")
            return content.strip(), False
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse inputs_json: {e}")
    except KeyError as e:
        raise ValueError(f"Missing required field in dataset row: {e}")
    except Exception as e:
        raise ValueError(f"Unexpected error extracting JIRA data: {e}")


def extract_jira_ticket_numbers(jira_raw_data: str, has_delimiters: bool = True) -> List[str]:
    """
    Extract JIRA ticket numbers from raw JIRA data.
    
    This function handles both XML formatted JIRA data (RSS format) and plain text.
    If delimiters were found, it tries XML parsing first, then falls back to regex.
    If no delimiters were found, it skips XML parsing and goes directly to regex.
    
    Expected XML structure (when has_delimiters=True):
    <rss version="0.92">
      <channel>
        <item>
          <title>[CSMVP-643] Issue Description</title>
          ...
        </item>
      </channel>
    </rss>
    
    Args:
        jira_raw_data: Raw JIRA data containing ticket information
        has_delimiters: Whether delimiters were found in the input (True = try XML first, False = regex only)
    
    Returns:
        List[str]: List of unique JIRA ticket numbers found
    """
    if not jira_raw_data:
        print("Warning: No JIRA data provided")
        return []
    
    try:
        # If delimiters were found, try XML parsing first
        if has_delimiters:
            try:
                print("🔍 Attempting XML parsing (delimiters found)...")
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
                
                print(f"✅ Found {len(unique_tickets)} unique JIRA ticket numbers from XML")
                if unique_tickets:
                    print(f"📋 Sample tickets: {unique_tickets[:5]}{'...' if len(unique_tickets) > 5 else ''}")
                
                return unique_tickets
                
            except ET.ParseError as xml_error:
                print(f"⚠️ XML parsing failed: {xml_error}")
                print("🔄 Falling back to regex pattern matching...")
        else:
            print("🔍 No delimiters found - using regex pattern matching directly...")
        
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
        
        method = "regex fallback" if has_delimiters else "regex (no delimiters)"
        print(f"✅ Found {len(unique_tickets)} unique JIRA ticket numbers from {method}")
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
        jira_raw_data, has_delimiters = extract_jira_data_from_input(dataset_row)
        if jira_raw_data:
            input_tickets = extract_jira_ticket_numbers(jira_raw_data, has_delimiters)
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
    Test function to demonstrate JIRA data extraction with sample XML data.
    This helps verify the function works before integrating with real datasets.
    """
    # Sample dataset row structure with XML format (simplified for testing)
    sample_row = {
        'id': 'test-123',
        'inputs_json': json.dumps({
            'messages': [{
                'role': 'system',
                'content': '''
                Some content before...
                
                <<START OF JIRA TICKETS>>
                
                <rss version="0.92">
                <channel>
                <title>Jira</title>
                <item>
                <title>[CSMVP-643] Irrelevant "Not Matched" Labels Displayed in ICP Tagging Explanation</title>
                <link>https://example.atlassian.net/browse/CSMVP-643</link>
                <key id="12336">CSMVP-643</key>
                <type id="10006">Bug</type>
                <status id="10012">Backlog</status>
                </item>
                <item>
                <title>[CSMVP-601] Counts don't Match</title>
                <link>https://example.atlassian.net/browse/CSMVP-601</link>
                <key id="12301">CSMVP-601</key>
                <type id="10006">Bug</type>
                <status id="10001">Done</status>
                </item>
                <item>
                <title>[CSMVP-636] Backend/Data Engagement Timeline</title>
                <link>https://example.atlassian.net/browse/CSMVP-636</link>
                <key id="12336">CSMVP-636</key>
                <type id="10001">Story</type>
                <status id="10002">In Progress</status>
                </item>
                </channel>
                </rss>
                
                <<END OF JIRA TICKETS>>
                
                Some content after...
                '''
            }]
        }),
        'outputs_json': '{"result": "Based on analysis of CSMVP-643 and CSMVP-601, we found issues. The CSMVP-999 was completed successfully."}'
    }
    
    # Sample dataset row structure WITHOUT delimiters (for testing no-delimiter scenario)
    sample_row_no_delimiters = {
        'id': 'test-no-delimiters',
        'inputs_json': json.dumps({
            'messages': [{
                'role': 'system',
                'content': '''
                Here are some JIRA tickets mentioned in various formats:
                - BUG-123 is a critical issue
                - FEAT-456 was implemented last week
                - The team is working on PROJ-789
                - Task CSMVP-101 needs review
                
                Some additional context about these tickets...
                '''
            }]
        }),
        'outputs_json': '{"result": "Analysis shows BUG-123 and FEAT-456 are resolved. NONEXISTENT-999 was also checked."}'
    }
    
    print("🧪 Testing JIRA extraction function...")
    print("=" * 70)
    
    try:
        jira_data, has_delimiters = extract_jira_data_from_input(sample_row)
        
        if jira_data:
            print(f"📊 Extracted JIRA data:")
            print(f"📏 Length: {len(jira_data)} characters")
            print(f"🔖 Has delimiters: {has_delimiters}")
            print(f"📝 Preview:")
            print(jira_data[:200] + "..." if len(jira_data) > 200 else jira_data)
            
            # Test ticket number extraction from input
            print(f"\n🎫 Testing ticket number extraction from input...")
            ticket_numbers = extract_jira_ticket_numbers(jira_data, has_delimiters)
            
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
        
        # Test the full truthfulness evaluation
        print(f"\n🔍 Testing full truthfulness evaluation...")
        score = evaluate_jira_truthfulness(sample_row)
        print(f"📊 Final truthfulness score: {score}")
        
        # Test scenario without delimiters
        print(f"\n" + "=" * 70)
        print("🧪 Testing scenario WITHOUT delimiters...")
        print("-" * 50)
        
        jira_data_no_delim, has_delimiters_no_delim = extract_jira_data_from_input(sample_row_no_delimiters)
        
        if jira_data_no_delim:
            print(f"📊 Extracted JIRA data (no delimiters):")
            print(f"📏 Length: {len(jira_data_no_delim)} characters")
            print(f"🔖 Has delimiters: {has_delimiters_no_delim}")
            print(f"📝 Preview:")
            print(jira_data_no_delim[:150] + "..." if len(jira_data_no_delim) > 150 else jira_data_no_delim)
            
            # Test ticket number extraction from input (should skip XML parsing)
            print(f"\n🎫 Testing ticket number extraction (no delimiters)...")
            ticket_numbers_no_delim = extract_jira_ticket_numbers(jira_data_no_delim, has_delimiters_no_delim)
            
            if ticket_numbers_no_delim:
                print(f"📋 Extracted {len(ticket_numbers_no_delim)} ticket numbers:")
                for i, ticket in enumerate(ticket_numbers_no_delim, 1):
                    print(f"   {i}. {ticket}")
            else:
                print("❌ No ticket numbers found")
            
            # Test full evaluation for no-delimiters scenario
            print(f"\n🔍 Testing full truthfulness evaluation (no delimiters)...")
            score_no_delim = evaluate_jira_truthfulness(sample_row_no_delimiters)
            print(f"📊 Final truthfulness score (no delimiters): {score_no_delim}")
        else:
            print("❌ No JIRA data extracted from input (no delimiters)")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")


if __name__ == "__main__":
    # Run test when script is executed directly
    test_jira_extraction() 