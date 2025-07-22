#!/usr/bin/env python3
"""
Test JIRA Evaluator with Real Dataset

Tests the extract_jira_data_from_input function with actual LangSmith dataset.
"""

import pandas as pd
import os
import glob
from jira_evaluator import extract_jira_data_from_input, extract_jira_ticket_numbers, extract_jira_references_from_output


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
        total_input_tickets = []
        total_output_references = []
        successful_extractions = 0
        row_results = []  # Store results for each row
        
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
                
                # Test ticket number extraction from input
                print(f"\n🎫 Extracting JIRA tickets from INPUT...")
                input_tickets = extract_jira_ticket_numbers(jira_data)
                
            else:
                input_tickets = []
                print("❌ No JIRA data found in input")
            
            # Test JIRA reference extraction from output
            print(f"\n🎯 Extracting JIRA references from OUTPUT...")
            output_references = extract_jira_references_from_output(current_row)
            
            # Store results for this row
            row_result = {
                'row_index': row_index + 1,
                'row_id': current_row['id'],
                'input_tickets': input_tickets,
                'output_references': output_references,
                'has_jira_data': len(input_tickets) > 0
            }
            row_results.append(row_result)
            
            # Add to totals
            total_input_tickets.extend(input_tickets)
            total_output_references.extend(output_references)
            
            # Show comparison for this row
            print(f"\n📊 ROW {row_index + 1} COMPARISON:")
            print(f"   📥 Input tickets found: {len(input_tickets)}")
            if input_tickets:
                sample_size = min(5, len(input_tickets))
                print(f"      Sample: {input_tickets[:sample_size]}")
                if len(input_tickets) > sample_size:
                    print(f"      ... and {len(input_tickets) - sample_size} more")
            
            print(f"   📤 Output references found: {len(output_references)}")
            if output_references:
                sample_size = min(5, len(output_references))
                print(f"      Sample: {output_references[:sample_size]}")
                if len(output_references) > sample_size:
                    print(f"      ... and {len(output_references) - sample_size} more")
            
            # Quick truthfulness check for this row
            if input_tickets and output_references:
                input_set = set(input_tickets)
                output_set = set(output_references)
                valid_refs = output_set.intersection(input_set)
                invalid_refs = output_set - input_set
                
                print(f"   ✅ Valid references: {len(valid_refs)} (AI mentioned real tickets)")
                print(f"   ❌ Invalid references: {len(invalid_refs)} (AI mentioned non-existent tickets)")
                
                if invalid_refs:
                    print(f"      🚨 Possibly hallucinated: {list(invalid_refs)[:3]}{'...' if len(invalid_refs) > 3 else ''}")
                if valid_refs:
                    print(f"      ✓ Correctly referenced: {list(valid_refs)[:3]}{'...' if len(valid_refs) > 3 else ''}")
            
            if input_tickets:
                successful_extractions += 1
        
        # Show detailed overall summary
        print(f"\n🎯 DETAILED ANALYSIS SUMMARY")
        print("=" * 80)
        print(f"📊 Rows processed: {num_rows}")
        print(f"✅ Rows with JIRA data: {successful_extractions}")
        print(f"📈 JIRA data success rate: {(successful_extractions/num_rows)*100:.1f}%")
        
        # Calculate unique tickets
        unique_input_tickets = list(set(total_input_tickets)) if total_input_tickets else []
        unique_output_references = list(set(total_output_references)) if total_output_references else []
        
        print(f"\n📥 INPUT ANALYSIS:")
        print(f"   🎫 Total unique tickets in source data: {len(unique_input_tickets)}")
        print(f"   🔢 Total ticket mentions: {len(total_input_tickets)}")
        if unique_input_tickets:
            sample_input = unique_input_tickets[:10]
            print(f"   📋 Sample tickets: {sample_input}")
            if len(unique_input_tickets) > 10:
                print(f"       ... and {len(unique_input_tickets) - 10} more")
        
        print(f"\n📤 OUTPUT ANALYSIS:")
        print(f"   🎫 Total unique AI references: {len(unique_output_references)}")
        print(f"   🔢 Total reference mentions: {len(total_output_references)}")
        if unique_output_references:
            sample_output = unique_output_references[:10]
            print(f"   📋 Sample references: {sample_output}")
            if len(unique_output_references) > 10:
                print(f"       ... and {len(unique_output_references) - 10} more")
        
        # Truthfulness analysis
        if unique_input_tickets and unique_output_references:
            input_set = set(unique_input_tickets)
            output_set = set(unique_output_references)
            
            valid_references = output_set.intersection(input_set)
            invalid_references = output_set - input_set
            unreferenced_tickets = input_set - output_set
            
            print(f"\n🔍 TRUTHFULNESS ANALYSIS:")
            print(f"   ✅ Valid AI references: {len(valid_references)} (AI mentioned real tickets)")
            print(f"   ❌ Invalid AI references: {len(invalid_references)} (AI possibly hallucinated)")
            print(f"   📋 Unreferenced tickets: {len(unreferenced_tickets)} (real tickets AI didn't mention)")
            
            if len(unique_output_references) > 0:
                accuracy_rate = (len(valid_references) / len(unique_output_references)) * 100
                print(f"   📊 AI Reference Accuracy: {accuracy_rate:.1f}%")
            
            if valid_references:
                print(f"\n   ✓ CORRECTLY REFERENCED:")
                valid_list = sorted(list(valid_references))
                for i, ticket in enumerate(valid_list[:10], 1):
                    print(f"     {i:2}. {ticket}")
                if len(valid_list) > 10:
                    print(f"        ... and {len(valid_list) - 10} more")
            
            if invalid_references:
                print(f"\n   🚨 POSSIBLY HALLUCINATED:")
                invalid_list = sorted(list(invalid_references))
                for i, ticket in enumerate(invalid_list[:10], 1):
                    print(f"     {i:2}. {ticket} ❌")
                if len(invalid_list) > 10:
                    print(f"        ... and {len(invalid_list) - 10} more")
        
        # Row-by-row breakdown
        print(f"\n📋 ROW-BY-ROW BREAKDOWN:")
        for result in row_results:
            truthful = "✅" if result['has_jira_data'] else "⚠️"
            input_count = len(result['input_tickets'])
            output_count = len(result['output_references'])
            
            if result['input_tickets'] and result['output_references']:
                input_set = set(result['input_tickets'])
                output_set = set(result['output_references'])
                valid = len(output_set.intersection(input_set))
                invalid = len(output_set - input_set)
                status = f"Valid: {valid}, Invalid: {invalid}"
            elif result['output_references'] and not result['input_tickets']:
                status = f"No input data to verify against"
            elif result['input_tickets'] and not result['output_references']:
                status = f"AI made no JIRA references"
            else:
                status = f"No JIRA data found"
            
            print(f"   {truthful} Row {result['row_index']}: Input({input_count}) → Output({output_count}) | {status}")
        
        # Project prefix analysis
        if unique_input_tickets or unique_output_references:
            all_unique_tickets = list(set(unique_input_tickets + unique_output_references))
            prefixes = {}
            for ticket in all_unique_tickets:
                prefix = ticket.split('-')[0]
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
            
            print(f"\n📂 PROJECT PREFIX ANALYSIS:")
            print(f"   Found {len(prefixes)} different project prefixes:")
            for prefix, count in sorted(prefixes.items()):
                print(f"     {prefix}: {count} tickets")
        
        else:
            print("\n❌ No JIRA tickets or references found in any row")
            
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