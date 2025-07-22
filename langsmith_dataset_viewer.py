#!/usr/bin/env python3
"""
LangSmith Dataset Viewer

This script connects to LangSmith, pulls a dataset locally, and displays it.
It demonstrates how to work with LangSmith datasets programmatically.
"""

import os
import sys
from typing import Optional, List, Dict, Any
import json
from datetime import datetime

try:
    from langsmith import Client
    from langsmith.schemas import Example
except ImportError:
    print("Error: langsmith package not found. Please install it with: pip install langsmith")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()
except ImportError:
    print("Note: python-dotenv not found. .env file support disabled.")

import pandas as pd


class LangSmithDatasetViewer:
    """A class to pull and display LangSmith datasets."""
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        """
        Initialize the LangSmith client.
        
        Args:
            api_key: LangSmith API key (if not provided, will look for LANGSMITH_API_KEY env var)
            api_url: LangSmith API URL (defaults to LangSmith cloud)
        """
        # Get API key from parameter or environment variable
        self.api_key = api_key or os.getenv("LANGSMITH_API_KEY")
        if not self.api_key:
            raise ValueError(
                "LangSmith API key not found. Please provide it as a parameter "
                "or set the LANGSMITH_API_KEY environment variable."
            )
        
        # Initialize the client
        try:
            self.client = Client(api_key=self.api_key, api_url=api_url)
            print("✅ Successfully connected to LangSmith")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to LangSmith: {e}")
    
    def list_datasets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List available datasets.
        
        Args:
            limit: Maximum number of datasets to return
            
        Returns:
            List of dataset information dictionaries
        """
        try:
            datasets = list(self.client.list_datasets(limit=limit))
            dataset_info = []
            
            for dataset in datasets:
                info = {
                    'id': str(dataset.id),
                    'name': dataset.name,
                    'description': dataset.description or "No description",
                    'created_at': dataset.created_at.strftime("%Y-%m-%d %H:%M:%S") if dataset.created_at else "Unknown",
                    'example_count': getattr(dataset, 'example_count', 'Unknown')
                }
                dataset_info.append(info)
            
            return dataset_info
        except Exception as e:
            print(f"❌ Error listing datasets: {e}")
            return []
    
    def pull_dataset(self, dataset_name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Pull a dataset from LangSmith.
        
        Args:
            dataset_name: Name of the dataset to pull
            limit: Maximum number of examples to pull (None for all)
            
        Returns:
            List of examples from the dataset
        """
        try:
            print(f"📥 Pulling dataset '{dataset_name}'...")
            
            # Get the dataset
            dataset = self.client.read_dataset(dataset_name=dataset_name)
            print(f"📊 Dataset found: {dataset.name}")
            print(f"📝 Description: {dataset.description or 'No description'}")
            
            # Get examples from the dataset
            examples = list(self.client.list_examples(dataset_name=dataset_name, limit=limit))
            
            # Convert examples to dictionaries
            example_data = []
            for example in examples:
                example_dict = {
                    'id': str(example.id),
                    'inputs': example.inputs,
                    'outputs': example.outputs,
                    'created_at': example.created_at.strftime("%Y-%m-%d %H:%M:%S") if example.created_at else "Unknown"
                }
                example_data.append(example_dict)
            
            print(f"✅ Successfully pulled {len(example_data)} examples")
            return example_data
            
        except Exception as e:
            print(f"❌ Error pulling dataset '{dataset_name}': {e}")
            return []
    
    def display_dataset(self, examples: List[Dict[str, Any]], max_display: int = 5):
        """
        Display dataset examples in a readable format.
        
        Args:
            examples: List of example dictionaries
            max_display: Maximum number of examples to display in detail
        """
        if not examples:
            print("No examples to display.")
            return
        
        print(f"\n📋 Dataset Summary:")
        print(f"Total examples: {len(examples)}")
        
        # Show first few examples in detail
        print(f"\n🔍 Displaying first {min(max_display, len(examples))} examples in detail:")
        print("=" * 80)
        
        for i, example in enumerate(examples[:max_display]):
            print(f"\nExample {i + 1}:")
            print(f"  ID: {example['id']}")
            print(f"  Created: {example['created_at']}")
            print(f"  Inputs: {json.dumps(example['inputs'], indent=4, ensure_ascii=False)}")
            print(f"  Outputs: {json.dumps(example['outputs'], indent=4, ensure_ascii=False)}")
            print("-" * 40)
        
        if len(examples) > max_display:
            print(f"\n... and {len(examples) - max_display} more examples")
    
    def export_to_csv(self, examples: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Export dataset to CSV file in the datasets folder.
        
        Args:
            examples: List of example dictionaries
            filename: Output filename (if None, will generate timestamp-based name)
            
        Returns:
            The full path of the file that was created
        """
        if not examples:
            print("No examples to export.")
            return ""
        
        # Create datasets directory if it doesn't exist
        datasets_dir = "datasets"
        if not os.path.exists(datasets_dir):
            os.makedirs(datasets_dir)
            print(f"📁 Created directory: {datasets_dir}")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"langsmith_dataset_{timestamp}.csv"
        
        # Ensure filename doesn't already include the path
        if not filename.startswith(datasets_dir):
            filepath = os.path.join(datasets_dir, filename)
        else:
            filepath = filename
        
        # Flatten the data for CSV export
        flattened_data = []
        for example in examples:
            row = {
                'id': example['id'],
                'created_at': example['created_at'],
                'inputs_json': json.dumps(example['inputs']),
                'outputs_json': json.dumps(example['outputs'])
            }
            flattened_data.append(row)
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(flattened_data)
        df.to_csv(filepath, index=False)
        
        print(f"💾 Dataset exported to: {filepath}")
        return filepath


def main():
    """Main function to demonstrate the LangSmith dataset viewer."""
    print("🚀 LangSmith Dataset Viewer")
    print("=" * 50)
    
    try:
        # Initialize the viewer
        viewer = LangSmithDatasetViewer()
        
        # List available datasets
        print("\n📂 Available datasets:")
        datasets = viewer.list_datasets(limit=10)
        
        if not datasets:
            print("No datasets found or unable to retrieve datasets.")
            return
        
        for i, dataset in enumerate(datasets, 1):
            print(f"{i}. {dataset['name']}")
            print(f"   Description: {dataset['description']}")
            print(f"   Created: {dataset['created_at']}")
            print(f"   Examples: {dataset['example_count']}")
            print()
        
        # Ask user to select a dataset
        if len(datasets) > 0:
            print(f"\n🎯 Select a dataset to pull:")
            
            # Get user selection
            while True:
                try:
                    choice = input(f"\nEnter dataset number (1-{len(datasets)}) or 'q' to quit: ").strip()
                    
                    if choice.lower() == 'q':
                        print("👋 Goodbye!")
                        return
                    
                    dataset_index = int(choice) - 1
                    if 0 <= dataset_index < len(datasets):
                        break
                    else:
                        print(f"❌ Please enter a number between 1 and {len(datasets)}")
                        
                except ValueError:
                    print("❌ Please enter a valid number or 'q' to quit")
            
            # Get selected dataset
            selected_dataset = datasets[dataset_index]
            dataset_name = selected_dataset['name']
            print(f"\n🎯 Selected: {dataset_name}")
            
            # Ask for limit
            while True:
                try:
                    limit_input = input(f"\nHow many examples to pull? (Enter number or 'all' for everything): ").strip()
                    
                    if limit_input.lower() == 'all':
                        limit = None
                        print("📥 Will pull all examples")
                        break
                    else:
                        limit = int(limit_input)
                        if limit > 0:
                            print(f"📥 Will pull {limit} examples")
                            break
                        else:
                            print("❌ Please enter a positive number")
                            
                except ValueError:
                    print("❌ Please enter a valid number or 'all'")
            
            # Pull the dataset
            examples = viewer.pull_dataset(dataset_name, limit=limit)
            
            if examples:
                # Display the dataset
                viewer.display_dataset(examples, max_display=3)
                
                # Export to CSV
                csv_filename = viewer.export_to_csv(examples)
                print(f"\n✨ Done! Check the '{csv_filename}' file for the complete dataset.")
            else:
                print("No examples found in the dataset.")
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\n💡 Quick Setup:")
        print("1. Get your API key from https://smith.langchain.com/")
        print("2. Set it as an environment variable: export LANGSMITH_API_KEY=your_key_here")
        print("3. Or pass it directly to the LangSmithDatasetViewer class")
        
    except ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print("Please check your internet connection and API key.")
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")


if __name__ == "__main__":
    main() 