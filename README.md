# JIRA Truthfulness Evaluator for LangSmith

A comprehensive evaluation system that detects AI hallucinations by verifying whether AI-generated reports contain only truthful JIRA ticket references. This tool compares JIRA tickets mentioned in AI outputs against actual tickets available in the input data, supporting both XML (RSS) and plain text formats.

## Features

- 🔍 **XML & Plain Text Support** - Handles both RSS XML format and plain text JIRA data
- 🎯 **Truthfulness Detection** - Identifies when AI models reference non-existent JIRA tickets
- 📊 **Comprehensive Evaluation** - Provides both simple binary scores and detailed analytics
- 🔄 **Automatic Fallback** - Gracefully handles format changes with XML-to-regex fallback
- 📈 **Batch Processing** - Test with large datasets using efficient batch processing
- 🛡️ **Production Ready** - Robust error handling suitable for LangSmith deployment
- 🎨 **Detailed Analytics** - Rich metrics including accuracy rates, format detection, and more

## What is JIRA Truthfulness Evaluation?

This system addresses a critical problem in AI applications: **AI hallucination of JIRA tickets**. When AI models generate reports or summaries about software projects, they sometimes reference JIRA tickets that don't actually exist, leading to confusion and incorrect information.

Our evaluator:
- **Compares AI output** against ground truth JIRA ticket data
- **Detects hallucinations** when AI references non-existent tickets
- **Provides confidence scores** for AI-generated content
- **Supports various formats** including XML (RSS) and plain text

## LangSmith Integration

[LangSmith](https://smith.langchain.com/) is a platform by LangChain for debugging, testing, evaluating, and monitoring LLM applications. This evaluator integrates seamlessly with LangSmith as a custom evaluator, providing:
- Real-time truthfulness scoring during AI model evaluation
- Detailed metrics for monitoring AI hallucination rates
- Batch evaluation capabilities for large datasets
- Production-ready deployment for continuous monitoring

## Prerequisites

- Python 3.7 or higher
- Basic understanding of JIRA ticket formats
- Dataset with JIRA ticket data (XML or plain text format)
- For LangSmith deployment: LangSmith account and API key

## Installation

1. **Clone or download this repository**

2. **Set up a virtual environment (Recommended):**

   ```bash
   # Create virtual environment
   python -m venv langsmith-env
   
   # Activate virtual environment
   # Windows (Command Prompt/PowerShell)
   langsmith-env\Scripts\activate
   
   # Windows (Git Bash)
   source langsmith-env/Scripts/activate
   ```

   > **Note**: You'll see `(langsmith-env)` in your terminal prompt when active.

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   > **Important**: Make sure your virtual environment is activated before installing dependencies!

## File Structure

The repository contains several key components:

- **`jira_evaluator.py`** - Development/testing version with verbose output
- **`jira_evaluator_final.py`** - Production-ready version for LangSmith deployment
- **`test_with_real_data.py`** - Tool for testing with actual CSV datasets
- **`datasets/`** - Directory containing your JIRA dataset files
- **`requirements.txt`** - Python dependencies

## Usage

### Testing with Development Version

Use `jira_evaluator.py` for development and testing:

```bash
# Test the built-in examples
python jira_evaluator.py

# This will run the test_jira_extraction() function which includes:
# - XML format parsing test
# - Plain text (no delimiters) test  
# - Truthfulness evaluation examples
```

### Testing with Real Data

Use `test_with_real_data.py` to test with your actual datasets:

```bash
python test_with_real_data.py
```

The script will:
1. **Find CSV files** in the `datasets/` directory
2. **Prompt for selection** if multiple files exist
3. **Ask how many rows** to process (or 'all' for complete dataset)
4. **Process in batches** for large datasets (batches of 5)
5. **Provide detailed analysis** including:
   - Delimiter detection (XML vs plain text)
   - JIRA ticket extraction results
   - Truthfulness evaluation scores
   - Comprehensive statistics

### LangSmith Deployment

For production use in LangSmith, use `jira_evaluator_final.py`:

```python
from jira_evaluator_final import perform_eval

# Binary truthfulness evaluation for LangSmith
def my_evaluator(run, example):
    return perform_eval(run, example)
    # Returns: {"truthfulness": 1 or 0}
```

### Programmatic Usage

You can also use the evaluator functions directly in your code:

```python
from jira_evaluator import evaluate_jira_truthfulness

# Example dataset row structure
dataset_row = {
    'id': 'example-123',
    'inputs_json': '{"messages": [{"role": "system", "content": "..."}]}',
    'outputs_json': '{"result": "Analysis mentions JIRA-123 and FAKE-999"}'
}

# Evaluate truthfulness
score = evaluate_jira_truthfulness(dataset_row)
print(f"Truthfulness score: {score}")  # 0 or 1
```

## How It Works

### Core Components

1. **JIRA Data Extraction**
   - Automatically detects XML (RSS) vs plain text format
   - Extracts JIRA tickets between `<<START OF JIRA TICKETS>>` and `<<END OF JIRA TICKETS>>` delimiters
   - Falls back to searching entire input if no delimiters found

2. **Key Functions:**
   - `extract_jira_data_from_input()` - Finds JIRA data and determines format
   - `extract_jira_ticket_numbers()` - Extracts ticket IDs with XML/regex parsing
   - `extract_jira_references_from_output()` - Finds JIRA references in AI output
   - `evaluate_jira_truthfulness()` - Compares input vs output for truthfulness

### Evaluation Process

1. **Input Processing**: Extract ground truth JIRA tickets from input data
2. **Format Detection**: Automatically identify XML (RSS) or plain text format
3. **Ticket Extraction**: Parse tickets using appropriate method (XML or regex)
4. **Output Analysis**: Find JIRA references in AI-generated content
5. **Truthfulness Check**: Compare output references against input tickets
6. **Scoring**: Return binary score (1 = truthful, 0 = contains hallucinations)

### Supported Data Formats

#### XML Format (RSS)
```xml
<<START OF JIRA TICKETS>>
<rss><channel>
  <item><title>[CSMVP-643] Bug in user authentication</title></item>
  <item><title>[PROJ-123] Feature request for dashboard</title></item>
</channel></rss>
<<END OF JIRA TICKETS>>
```

#### Plain Text Format
```text
Here are the relevant JIRA tickets:
- BUG-123: Critical authentication issue
- FEAT-456: Dashboard enhancement request
- PROJ-789: Database optimization task
```

### Expected Input Structure

Your dataset should contain rows with:
- `id`: Unique identifier for the example
- `inputs_json`: JSON string containing the input with JIRA data
- `outputs_json`: JSON string containing AI-generated output to evaluate

## Example Output

### Testing with `test_with_real_data.py`

```
🚀 JIRA Evaluator Test Suite
============================================================
🧪 Testing JIRA extraction with real dataset...

📂 Loading dataset: datasets/langsmith_dataset_20250725_155130.csv
📊 Dataset loaded: 142 rows

📊 Dataset contains 142 total rows
How many rows to test? (1-5, or 'all' for ALL 142 rows): all
✅ Will process ALL 142 rows in batches of 5 for better readability

🎯 Testing with 142 rows...
📦 Processing in batches for better performance and readability

🗂️ BATCH 1/29 (Rows 1-5)
==================================================

📄 ROW 1/142
----------------------------------------
🆔 Row ID: 2b5c3e7a-8f9d-4e1a-b2c3-d4e5f6789abc
🔖 Has delimiters: True
🔍 Processing method: XML parsing (then regex fallback if needed)
🎫 Found 15 unique JIRA ticket numbers from XML parsing
✅ Row 1: 🔖 XML | Input(15) → Output(3) | Valid: 3, Invalid: 0 | Score: 1 (TRUTHFUL)

📄 ROW 2/142
----------------------------------------
🆔 Row ID: 3c6d4e8b-9f0e-5f2b-c3d4-e5f6g7890def
🔖 Has delimiters: False
🔍 Processing method: Direct regex pattern matching
🎫 Found 8 unique JIRA ticket numbers from regex (no delimiters)
❌ Row 2: 📝 Text | Input(8) → Output(5) | Valid: 3, Invalid: 2 | Score: 0 (UNTRUTHFUL)

📊 BATCH 1 SUMMARY:
   ✅ Rows with JIRA data: 5/5
   🎯 Truthful rows: 4/5
   📈 Progress: 5/142 rows (3.5%)

🎉 PROCESSING COMPLETE!
✅ Successfully processed all 142 rows

🎯 DETAILED ANALYSIS SUMMARY
================================================================================
📊 Rows processed: 142
✅ Rows with JIRA data: 138
📈 JIRA data success rate: 97.2%

🔍 DELIMITER ANALYSIS:
   🔖 Rows with delimiters (XML format): 95
   📝 Rows without delimiters (plain text): 43
   📊 Delimiter presence rate: 68.8%

🏆 OVERALL TRUTHFULNESS SCORE:
   📊 Truthful rows: 124/138
   📈 Truthfulness rate: 89.9%

🔍 TRUTHFULNESS ANALYSIS:
   ✅ Valid AI references: 1,247 (AI mentioned real tickets)
   ❌ Invalid AI references: 43 (AI possibly hallucinated)
   📊 AI Reference Accuracy: 96.7%
```

### Simple Evaluation Output

```python
result = perform_eval(run, example)
print(result)
# Output: {"truthfulness": 1}
```



## Troubleshooting

### Common Issues

1. **"No JIRA data found in input"**
   - Verify your dataset contains JIRA ticket delimiters: `<<START OF JIRA TICKETS>>` and `<<END OF JIRA TICKETS>>`
   - Check that JIRA tickets follow expected patterns: `PROJECT-123` format
   - Ensure input data is properly formatted JSON in the `inputs_json` column

2. **"XML parsing failed"**
   - This is normal for plain text data - the system automatically falls back to regex parsing
   - If consistently failing, verify XML structure follows RSS format: `<item><title>[TICKET-123] Description</title></item>`

3. **"No datasets found" (when using test_with_real_data.py)**
   - Make sure you have CSV files in the `datasets/` directory
   - Verify CSV files contain required columns: `id`, `inputs_json`, `outputs_json`

4. **Low truthfulness scores**
   - Check if AI output contains JIRA references not present in input data
   - Verify input data contains all legitimate JIRA tickets the AI should reference
   - Use the development version (`jira_evaluator.py`) for detailed debugging information

5. **Performance issues with large datasets**
   - Use the batch processing feature (built into test_with_real_data.py)
   - Consider testing with smaller subsets first using the row limit option

### Data Format Validation

Ensure your CSV dataset has the correct structure:

```csv
id,inputs_json,outputs_json
"example-1","{\"messages\":[{\"role\":\"system\",\"content\":\"...<<START OF JIRA TICKETS>>...\"}]}","{\"result\":\"Analysis mentions PROJ-123\"}"
```

### Getting Help

- Check function documentation within the code files
- Review the built-in test examples in `jira_evaluator.py`
- Verify your JIRA ticket patterns match the regex: `[A-Z]{2,10}-\d{1,6}`

## Customization

### Modifying JIRA Ticket Patterns

Customize the regex pattern to match your specific JIRA ticket format:

```python
# In jira_evaluator.py or jira_evaluator_final.py, modify this pattern:
ticket_pattern = r'\b[A-Z]{2,10}-\d{1,6}\b'

# Examples of custom patterns:
# For tickets like "MYPROJECT-12345":
ticket_pattern = r'\bMYPROJECT-\d{1,6}\b'

# For multiple specific projects:
ticket_pattern = r'\b(?:PROJ|BUG|FEAT|TASK)-\d{1,6}\b'

# For different number ranges:
ticket_pattern = r'\b[A-Z]{2,8}-\d{1,10}\b'
```

### Custom Delimiters

Change the delimiters used to identify JIRA data sections:

```python
# In extract_jira_data_from_input function:
start_delimiter = "<<START OF JIRA TICKETS>>"
end_delimiter = "<<END OF JIRA TICKETS>>"

# Customize to your format:
start_delimiter = "--- JIRA TICKETS BEGIN ---"
end_delimiter = "--- JIRA TICKETS END ---"
```

### Adding Custom Evaluation Metrics

Extend the simple evaluator with additional metrics if needed:

```python
def custom_evaluator(run, example):
    # Get the basic truthfulness result
    result = perform_eval(run, example)
    
    # Add custom metrics if needed
    result["custom_metric"] = calculate_my_metric(run, example)
    result["confidence_score"] = calculate_confidence(result)
    
    return result
```

### Batch Size Configuration

Adjust batch processing size in `test_with_real_data.py`:

```python
# Change this line in test_with_real_data.py:
batch_size = 5  # Modify to your preferred batch size
```

## LangSmith Deployment Guide

### Setting up as a Custom Evaluator

1. **Upload the evaluator file** to your LangSmith workspace
2. **Create a new evaluator** in the LangSmith UI
3. **Configure the evaluator function**:

```python
# Binary truthfulness evaluation
from jira_evaluator_final import perform_eval as evaluator
```

### Production Considerations

- Use `jira_evaluator_final.py` for production (optimized, less verbose)
- Use `jira_evaluator.py` for development and debugging (detailed logging)
- Monitor evaluation performance with large datasets
- Consider implementing caching for repeated evaluations

## Security Notes

- The included `.gitignore` file protects sensitive data:
  - Dataset files (`datasets/` folder and `*.csv` files)  
  - Virtual environment files
  - Temporary test files
- Be mindful of data privacy when working with JIRA ticket data
- Ensure JIRA ticket information complies with your organization's data policies
- Review AI outputs for sensitive information before evaluation

## Advanced Features

### Format Detection

The evaluator automatically detects and handles:
- **XML Format**: RSS feeds with `<item><title>[TICKET-123] Description</title></item>`
- **Plain Text**: JIRA tickets in any text format matching the regex pattern
- **Mixed Datasets**: Automatically processes both formats in the same dataset

### Error Handling

Robust error handling ensures:
- **Conservative scoring**: Returns 0 (untruthful) on parsing errors
- **Graceful fallbacks**: XML parsing failures fall back to regex
- **Detailed error reporting**: Error information included in detailed evaluation results

## License

This evaluator is provided as-is for educational and production use. Please ensure compliance with your organization's policies regarding JIRA data handling and AI evaluation practices.

---

**Happy JIRA truthfulness evaluation! 🎯** 