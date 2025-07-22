#!/usr/bin/env python3
"""
Test JIRA Evaluator with Real Dataset

Tests the extract_jira_data_from_input function with actual LangSmith dataset.
"""

import pandas as pd
import os
import glob
from jira_evaluator import extract_jira_data_from_input, extract_jira_ticket_numbers


def find_csv_files():
    """Find all CSV files in the datasets directory."""
    datasets_dir = "datasets"
    if not os.path.exists(datasets_dir):
        return []
    
    csv_files = glob.glob(os.path.join(datasets_dir, "*.csv"))
    return csv_files


def select_csv_file(csv_files):
    """Let user select which CSV file to test with."""
    if not csv_files:
        print("❌ No CSV files found in datasets/ directory")
        return None
    
    if len(csv_files) == 1:
        print(f"📁 Found 1 CSV file: {csv_files[0]}")
        return csv_files[0]
    
    print(f"📁 Found {len(csv_files)} CSV files:")
    for i, file in enumerate(csv_files, 1):
        file_size = os.path.getsize(file) / (1024 * 1024)  # MB
        print(f"   {i}. {os.path.basename(file)} ({file_size:.1f} MB)")
    
    while True:
        try:
            choice = input(f"\nSelect file number (1-{len(csv_files)}) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                return None
            
            file_index = int(choice) - 1
            if 0 <= file_index < len(csv_files):
                return csv_files[file_index]
            else:
                print(f"❌ Please enter a number between 1 and {len(csv_files)}")
        except ValueError:
            print("❌ Please enter a valid number or 'q' to quit")


def test_with_real_dataset():
    """
    Test the JIRA extraction function with the real sample dataset.
    """
    print("🧪 Testing JIRA extraction with real dataset...")
    print("=" * 60)
    
    # Find and select CSV file
    csv_files = find_csv_files()
    csv_path = select_csv_file(csv_files)
    
    if not csv_path:
        print("👋 No file selected. Exiting...")
        return
    
    try:
        print(f"\n📂 Loading dataset: {csv_path}")
        
        df = pd.read_csv(csv_path)
        print(f"📊 Dataset loaded: {len(df)} rows")
        
        # Show dataset structure
        print(f"\n📋 Dataset columns: {list(df.columns)}")
        print(f"📏 Sample row ID: {df.iloc[0]['id']}")
        
        # Ask user how many rows to test
        while True:
            try:
                max_rows = min(len(df), 5)  # Limit to 5 rows max
                rows_input = input(f"\nHow many rows to test? (1-{max_rows}, or 'all' for {max_rows}): ").strip()
                
                if rows_input.lower() == 'all':
                    num_rows = max_rows
                    break
                else:
                    num_rows = int(rows_input)
                    if 1 <= num_rows <= max_rows:
                        break
                    else:
                        print(f"❌ Please enter a number between 1 and {max_rows}")
            except ValueError:
                print("❌ Please enter a valid number or 'all'")
        
        print(f"\n🎯 Testing with {num_rows} row{'s' if num_rows > 1 else ''}...")
        print("=" * 60)
        
        # Test with selected number of rows
        total_tickets_found = []
        successful_extractions = 0
        
        for row_index in range(num_rows):
            print(f"\n📄 ROW {row_index + 1}/{num_rows}")
            print("-" * 40)
            
            # Convert the pandas row to a dictionary (this is what our function expects)
            current_row = df.iloc[row_index].to_dict()
            print(f"🆔 Row ID: {current_row['id']}")
        
            # Show some info about the inputs_json
            inputs_json_preview = current_row['inputs_json'][:150] + "..." if len(current_row['inputs_json']) > 150 else current_row['inputs_json']
            print(f"📝 inputs_json preview: {inputs_json_preview}")
            print(f"📏 inputs_json length: {len(current_row['inputs_json'])} characters")
            
            # Extract JIRA data
            print(f"\n⚡ Extracting JIRA data...")
            jira_data = extract_jira_data_from_input(current_row)
            
            if jira_data:
                successful_extractions += 1
                print(f"✅ SUCCESS! JIRA data extracted")
                print(f"📏 JIRA data length: {len(jira_data)} characters")
                
                # Only show preview for first row to avoid too much output
                if row_index == 0:
                    print(f"\n📄 JIRA Data Preview (first 300 characters):")
                    print("-" * 50)
                    preview = jira_data[:300] + "\n..." if len(jira_data) > 300 else jira_data
                    print(preview)
                
                # Test ticket number extraction
                print(f"\n🎫 Extracting ticket numbers...")
                ticket_numbers = extract_jira_ticket_numbers(jira_data)
                
                if ticket_numbers:
                    total_tickets_found.extend(ticket_numbers)
                    print(f"✅ Found {len(ticket_numbers)} unique tickets in this row")
                    
                    # Show first few tickets for each row
                    sample_size = min(5, len(ticket_numbers))
                    print(f"📋 Sample tickets: {ticket_numbers[:sample_size]}")
                    if len(ticket_numbers) > sample_size:
                        print(f"   ... and {len(ticket_numbers) - sample_size} more")
                        
                else:
                    print("❌ No ticket numbers found in this row")
                
            else:
                print("❌ No JIRA data found in this row")
        
        # Show overall summary
        print(f"\n🎯 OVERALL SUMMARY")
        print("=" * 60)
        print(f"📊 Rows processed: {num_rows}")
        print(f"✅ Successful extractions: {successful_extractions}")
        print(f"📈 Success rate: {(successful_extractions/num_rows)*100:.1f}%")
        
        if total_tickets_found:
            # Remove duplicates across all rows
            unique_total_tickets = list(set(total_tickets_found))
            print(f"🎫 Total unique tickets found: {len(unique_total_tickets)}")
            print(f"🔢 Total ticket references: {len(total_tickets_found)}")
            
            # Group by project prefix
            prefixes = {}
            for ticket in unique_total_tickets:
                prefix = ticket.split('-')[0]
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
            
            print(f"📂 Project prefixes found: {len(prefixes)}")
            for prefix, count in sorted(prefixes.items()):
                print(f"   {prefix}: {count} unique tickets")
                
            # Show sample of all unique tickets
            print(f"\n📋 Sample of all unique tickets found:")
            sample_size = min(15, len(unique_total_tickets))
            for i, ticket in enumerate(sorted(unique_total_tickets)[:sample_size], 1):
                print(f"   {i:2}. {ticket}")
            
            if len(unique_total_tickets) > sample_size:
                print(f"   ... and {len(unique_total_tickets) - sample_size} more tickets")
        else:
            print("❌ No tickets found in any row")
            
    except FileNotFoundError:
        print(f"❌ Dataset file not found: {csv_path}")
        print("💡 Make sure you have a CSV file in the datasets/ folder")
        
    except pd.errors.EmptyDataError:
        print(f"❌ The CSV file appears to be empty: {csv_path}")
        
    except pd.errors.ParserError as e:
        print(f"❌ Error parsing CSV file: {e}")
        print("💡 The CSV file might be corrupted or have formatting issues")
        
    except KeyError as e:
        print(f"❌ Missing expected column in dataset: {e}")
        print("💡 Make sure the CSV has 'id', 'inputs_json', and 'outputs_json' columns")
        
    except MemoryError:
        print("❌ Not enough memory to load the dataset")
        print("💡 Try with a smaller CSV file or increase available memory")
        
    except Exception as e:
        print(f"❌ Unexpected error during testing: {e}")
        print("\n🔍 Full error details:")
        import traceback
        traceback.print_exc()
        print("\n💡 If this persists, check that:")
        print("   - Your virtual environment is activated")
        print("   - All dependencies are installed (pip install -r requirements.txt)")
        print("   - The CSV file is valid and not corrupted")


def main():
    """Main function with additional setup checks."""
    print("🚀 JIRA Evaluator Test Suite")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("jira_evaluator.py"):
        print("❌ jira_evaluator.py not found!")
        print("💡 Make sure you're running this from the project root directory")
        return
    
    # Check if datasets directory exists
    if not os.path.exists("datasets"):
        print("❌ datasets/ directory not found!")
        print("💡 Make sure you have the datasets folder with CSV files")
        return
    
    # Run the test
    try:
        test_with_real_dataset()
        print(f"\n✨ Test completed successfully!")
        print("💡 Next step: Build the output JIRA reference extraction function")
        
    except KeyboardInterrupt:
        print(f"\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")


if __name__ == "__main__":
    main() 