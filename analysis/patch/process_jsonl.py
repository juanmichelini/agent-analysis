#!/usr/bin/env python3
"""
CLI script to process output.jsonl files and split git patches into fix and test patches.
"""
import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any

from analysis.patch.splitter import split_patch


def process_jsonl_file(input_path: str) -> None:
    """
    Process a jsonl file, splitting git patches into fix and test patches.
    
    Args:
        input_path (str): Path to the input jsonl file
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Create output path in the same directory
    output_path = input_path.parent / f"{input_path.stem}_swt{input_path.suffix}"
    
    # Process the file
    with open(input_path, 'r', encoding='utf-8') as f_in, \
         open(output_path, 'w', encoding='utf-8') as f_out:
        
        for line in f_in:
            try:
                data = json.loads(line.strip())
                
                # Check if the line contains test_result with git_patch
                if 'test_result' in data and 'git_patch' in data['test_result']:
                    original_patch = data['test_result']['git_patch']
                    
                    # Split the patch
                    fix_patch, test_patch = split_patch(original_patch)
                    
                    # Replace the git_patch with the test_patch
                    data['test_result']['git_patch'] = test_patch
                
                # Write the modified (or original) line to the output file
                f_out.write(json.dumps(data) + '\n')
                
            except json.JSONDecodeError:
                # If the line is not valid JSON, write it as is
                f_out.write(line)
    
    print(f"Processed {input_path} -> {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Process JSONL files to split git patches")
    parser.add_argument("input_path", help="Path to the input JSONL file")
    
    args = parser.parse_args()
    process_jsonl_file(args.input_path)


if __name__ == "__main__":
    main()