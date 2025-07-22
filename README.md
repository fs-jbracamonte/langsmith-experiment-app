# LangSmith Dataset Viewer

A Python script that connects to LangSmith, pulls datasets locally, and displays them in a readable format. This tool is perfect for exploring and analyzing your LangSmith datasets programmatically.

## Features

- 🔍 **List available datasets** - Browse all datasets in your LangSmith account
- 📥 **Pull datasets locally** - Download dataset examples with configurable limits
- 📊 **Display dataset contents** - View examples in a formatted, readable way
- 💾 **Export to CSV** - Save datasets locally in organized folders for further analysis
- 🛡️ **Error handling** - Robust error handling with helpful messages
- 🎨 **Beautiful output** - Clean, emoji-enhanced console output

## What is LangSmith?

[LangSmith](https://smith.langchain.com/) is a platform by LangChain for debugging, testing, evaluating, and monitoring LLM applications. It provides:
- Dataset management for training and evaluation
- Experiment tracking and comparison
- Production monitoring and analytics
- Collaborative debugging tools

## Prerequisites

- Python 3.7 or higher
- A LangSmith account and API key
- Internet connection

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

4. **Get your LangSmith API key:**
   - Go to [https://smith.langchain.com/](https://smith.langchain.com/)
   - Sign in to your account
   - Navigate to Settings → API Keys
   - Create a new API key or copy an existing one

5. **Set up your API key** (choose one method):

   **Method A: .env File (Recommended)**
   Create a `.env` file in your project directory:
   ```bash
   LANGSMITH_API_KEY=your_api_key_here
   ```

   **Method B: Environment Variable**
   ```bash
   # On Windows (PowerShell)
   $env:LANGSMITH_API_KEY="your_api_key_here"
   
   # On Windows (Command Prompt)
   set LANGSMITH_API_KEY=your_api_key_here
   
   # On Windows (Git Bash)
   export LANGSMITH_API_KEY=your_api_key_here
   ```

   **Method C: Direct Parameter**
   Modify the script to pass your API key directly:
   ```python
   viewer = LangSmithDatasetViewer(api_key="your_api_key_here")
   ```

## Usage

### Basic Usage

Run the script to interactively select and pull datasets:

```bash
python langsmith_dataset_viewer.py
```

The script will:
1. List all available datasets with numbers
2. Prompt you to select which dataset to pull
3. Ask how many examples you want (or 'all' for everything)
4. Display the results and export to CSV

### Advanced Usage

You can also use the script as a module in your own code:

```python
from langsmith_dataset_viewer import LangSmithDatasetViewer

# Initialize the viewer
viewer = LangSmithDatasetViewer()

# List all available datasets
datasets = viewer.list_datasets(limit=20)
print(f"Found {len(datasets)} datasets")

# Pull a specific dataset
examples = viewer.pull_dataset("my-dataset-name", limit=50)

# Display the dataset
viewer.display_dataset(examples, max_display=10)

# Export to CSV (will be saved in datasets/ folder)
csv_file = viewer.export_to_csv(examples, "my_dataset.csv")
```

## Script Explanation

### Core Components

1. **LangSmithDatasetViewer Class**
   - Main class that handles all LangSmith interactions
   - Manages authentication and API connections
   - Provides methods for listing, pulling, and displaying datasets

2. **Key Methods:**
   - `list_datasets()` - Retrieves available datasets from your account
   - `pull_dataset()` - Downloads examples from a specific dataset
   - `display_dataset()` - Shows dataset contents in the console
   - `export_to_csv()` - Saves dataset to a CSV file for analysis

### How it Works

1. **Authentication**: The script connects to LangSmith using your API key
2. **Dataset Discovery**: Lists all available datasets in your account
3. **Data Retrieval**: Pulls examples from the first dataset (or specified dataset)
4. **Display**: Shows dataset information and example contents
5. **Export**: Saves the data to a timestamped CSV file

### Data Structure

Each dataset example contains:
- **ID**: Unique identifier for the example
- **Inputs**: The input data (questions, prompts, etc.)
- **Outputs**: The expected or actual outputs
- **Created Date**: When the example was created

### CSV Export Format

CSV files are automatically saved in the `datasets/` folder. The exported CSV contains:
- `id`: Example ID
- `created_at`: Creation timestamp
- `inputs_json`: JSON string of input data
- `outputs_json`: JSON string of output data

## Example Output

```
🚀 LangSmith Dataset Viewer
==================================================
✅ Successfully connected to LangSmith

📂 Available datasets:
1. qa-evaluation-set
   Description: Question-answering evaluation dataset
   Created: 2024-01-15 10:30:45
   Examples: 150

2. customer-support-data
   Description: Customer support conversations
   Created: 2024-01-20 14:22:30
   Examples: 500

🎯 Select a dataset to pull:

Enter dataset number (1-2) or 'q' to quit: 1

🎯 Selected: qa-evaluation-set

How many examples to pull? (Enter number or 'all' for everything): 50
📥 Will pull 50 examples

📥 Pulling dataset 'qa-evaluation-set'...
📊 Dataset found: qa-evaluation-set
📝 Description: Question-answering evaluation dataset
✅ Successfully pulled 50 examples

📋 Dataset Summary:
Total examples: 50

🔍 Displaying first 3 examples in detail:
================================================================================

Example 1:
  ID: 550e8400-e29b-41d4-a716-446655440000
  Created: 2024-01-15 10:30:45
  Inputs: {
      "question": "What is the capital of France?"
  }
  Outputs: {
      "answer": "Paris"
  }

💾 Dataset exported to: datasets/langsmith_dataset_20240122_143052.csv
✨ Done! Check the 'datasets/langsmith_dataset_20240122_143052.csv' file for the complete dataset.
```

## Troubleshooting

### Common Issues

1. **"langsmith package not found"**
   ```bash
   pip install langsmith
   ```

2. **"LangSmith API key not found"**
   - Make sure you've set the LANGSMITH_API_KEY environment variable
   - Check that the API key is valid and active

3. **"Failed to connect to LangSmith"**
   - Verify your internet connection
   - Check if your API key has the correct permissions
   - Ensure you're not behind a firewall blocking the connection

4. **"No datasets found"**
   - Make sure you have datasets in your LangSmith account
   - Check that your API key has read permissions

### Getting Help

- Check the [LangSmith Documentation](https://docs.smith.langchain.com/)
- Visit the [LangChain Discord](https://discord.gg/langchain) for community support
- Review your API key permissions in the LangSmith dashboard

## Customization

### Modifying Display Limits

Change the number of datasets or examples shown:

```python
# Show more datasets
datasets = viewer.list_datasets(limit=50)

# Pull more examples
examples = viewer.pull_dataset(dataset_name, limit=100)

# Display more examples in detail
viewer.display_dataset(examples, max_display=10)
```

### Custom Export Formats

You can extend the script to export in different formats:

```python
import json

# Export to JSON
def export_to_json(examples, filename):
    with open(filename, 'w') as f:
        json.dump(examples, f, indent=2)
```

## Security Notes

- Keep your API key secure and never commit it to version control
- The included `.gitignore` file protects sensitive data:
  - API keys (`.env` files)
  - Dataset exports (`datasets/` folder and `*.csv` files)
  - Virtual environment files
- Use environment variables or .env files for production deployments
- Regularly rotate your API keys
- Be mindful of data privacy when exporting datasets

## License

This script is provided as-is for educational and development purposes. Please ensure compliance with LangSmith's terms of service when using their API.

---

**Happy dataset exploring! 🚀** 