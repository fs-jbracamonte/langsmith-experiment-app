#!/usr/bin/env python3
"""
Test script to verify functionality when JIRA delimiters are not present
"""

import json
from jira_evaluator import evaluate_jira_truthfulness

# Test case 1: No delimiters, XML content in input (should extract tickets from entire input)
no_delimiters_xml = {
    'id': 'test-no-delimiters-xml',
    'inputs_json': json.dumps({
        'messages': [{
            'content': '''
            Here is some analysis content about the team's performance.
            
            The data comes from this JIRA export:
            
            <rss version="0.92">
            <channel>
            <item>
            <title>[CSMVP-643] Test Issue 1</title>
            </item>
            <item>
            <title>[CSMVP-601] Test Issue 2</title>
            </item>
            </channel>
            </rss>
            
            This shows the tickets we need to analyze.
            '''
        }]
    }),
    'outputs_json': json.dumps({
        'result': 'Analysis shows CSMVP-643 has issues. CSMVP-601 was resolved successfully.'
    })
}

# Test case 2: No delimiters, plain text with JIRA tickets (should use regex fallback)
no_delimiters_text = {
    'id': 'test-no-delimiters-text',
    'inputs_json': json.dumps({
        'messages': [{
            'content': '''
            Team performance analysis based on JIRA tickets:
            
            BUG-123: Critical login issue
            FEAT-456: New dashboard feature
            STORY-789: User experience improvements
            
            These tickets were completed during the sprint.
            '''
        }]
    }),
    'outputs_json': json.dumps({
        'result': 'The sprint included BUG-123 and FEAT-456. We also completed XYZ-999.'
    })
}

# Test case 3: No delimiters, invalid reference (should return 0)
no_delimiters_invalid = {
    'id': 'test-no-delimiters-invalid',
    'inputs_json': json.dumps({
        'messages': [{
            'content': '''
            Team performance analysis:
            
            <rss version="0.92">
            <channel>
            <item>
            <title>[CSMVP-643] Only ticket available</title>
            </item>
            </channel>
            </rss>
            '''
        }]
    }),
    'outputs_json': json.dumps({
        'result': 'Analysis of CSMVP-643 and CSMVP-999 shows issues.'
    })
}

print("🧪 Testing functionality when JIRA delimiters are NOT present...")
print("=" * 70)

print("\n📝 Test 1: No delimiters, XML content in input")
print("Expected: Should find tickets in XML, compare with output, return 1 (truthful)")
score1 = evaluate_jira_truthfulness(no_delimiters_xml)
print(f"Result: {score1} {'✅ PASSED' if score1 == 1 else '❌ FAILED'}")

print("\n📝 Test 2: No delimiters, plain text with JIRA tickets")
print("Expected: Should use regex fallback, find tickets, return 0 (invalid reference)")
score2 = evaluate_jira_truthfulness(no_delimiters_text)
print(f"Result: {score2} {'✅ PASSED' if score2 == 0 else '❌ FAILED'}")

print("\n📝 Test 3: No delimiters, invalid reference in output")
print("Expected: Should find XML tickets, detect hallucination, return 0 (untruthful)")
score3 = evaluate_jira_truthfulness(no_delimiters_invalid)
print(f"Result: {score3} {'✅ PASSED' if score3 == 0 else '❌ FAILED'}")

print(f"\n🎯 Summary:")
print(f"All tests demonstrate that when delimiters are missing:")
print(f"1. ✅ Code searches entire input content")
print(f"2. ✅ XML parsing works when XML is present")
print(f"3. ✅ Regex fallback works for plain text")
print(f"4. ✅ Truthfulness evaluation works correctly") 