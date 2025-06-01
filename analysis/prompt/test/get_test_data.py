#!/usr/bin/env python3
"""
Script to fetch data from SWE-bench_Verified dataset and create JSONL files for testing.
"""
import json
import os
from datasets import load_dataset

def main():
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    
    # Load the dataset
    print("Loading SWE-bench_Verified dataset...")
    dataset = load_dataset("princeton-nlp/SWE-bench_Verified")
    
    # Initialize lists to store data
    fix_data = []
    test_data = []
    all_data = []
    
    # Process the dataset
    print("Processing dataset...")
    for split in dataset.keys():
        for item in dataset[split]:
            instance_id = item.get('instance_id', '')
            problem_statement = item.get('problem_statement', '')
            patch = item.get('patch', '')
            test_patch = item.get('test_patch', '')
            
            # Create entries for each dataset
            if problem_statement and patch:
                fix_data.append({
                    'instance_id': instance_id,
                    'input': problem_statement,
                    'expected_output': patch
                })
            
            if problem_statement and test_patch:
                test_data.append({
                    'instance_id': instance_id,
                    'input': problem_statement,
                    'expected_output': test_patch
                })
            
            # Create entries for the combined dataset
            if problem_statement and patch and test_patch:
                all_data.append({
                    'instance_id': instance_id,
                    'input': problem_statement,
                    'expected_output': f"{test_patch}\n\n{patch}"
                })
    
    # Write to JSONL files
    fix_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fix_dataset.jsonl')
    test_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_dataset.jsonl')
    all_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'all_dataset.jsonl')
    
    print(f"Writing {len(fix_data)} entries to fix_dataset.jsonl...")
    with open(fix_path, 'w') as f:
        for item in fix_data:
            f.write(json.dumps(item) + '\n')
    
    print(f"Writing {len(test_data)} entries to test_dataset.jsonl...")
    with open(test_path, 'w') as f:
        for item in test_data:
            f.write(json.dumps(item) + '\n')
    
    print(f"Writing {len(all_data)} entries to all_dataset.jsonl...")
    with open(all_path, 'w') as f:
        for item in all_data:
            f.write(json.dumps(item) + '\n')
    
    print("Done!")

if __name__ == "__main__":
    main()