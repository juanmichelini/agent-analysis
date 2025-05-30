#!/usr/bin/env python3
"""
CLI script to process output.jsonl files and split git patches into fix and test patches.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, List

from analysis.patch.splitter import split_patch


def process_jsonl_file(input_path: str, verbose: bool = False) -> None:
    """
    Process a jsonl file, splitting git patches into fix and test patches.
    
    Args:
        input_path (str): Path to the input jsonl file
        verbose (bool): Whether to print verbose debugging information
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Create output path in the same directory
    output_path = input_path.parent / f"{input_path.stem}_swt{input_path.suffix}"
    
    # Statistics
    total_lines = 0
    processed_lines = 0
    lines_with_patches = 0
    lines_with_test_patches = 0
    
    # Process the file
    with open(input_path, 'r', encoding='utf-8') as f_in, \
         open(output_path, 'w', encoding='utf-8') as f_out:
        
        for line_num, line in enumerate(f_in, 1):
            total_lines += 1
            try:
                data = json.loads(line.strip())
                processed_lines += 1
                
                # Check if the line contains test_result with git_patch
                if 'test_result' in data and isinstance(data['test_result'], dict) and 'git_patch' in data['test_result']:
                    original_patch = data['test_result']['git_patch']
                    lines_with_patches += 1
                    
                    if verbose:
                        print(f"Line {line_num}: Found git_patch of length {len(original_patch)}")
                    
                    if original_patch and len(original_patch.strip()) > 0:
                        # Split the patch
                        fix_patch, test_patch = split_patch(original_patch)
                        
                        if test_patch and len(test_patch.strip()) > 0:
                            lines_with_test_patches += 1
                            if verbose:
                                print(f"Line {line_num}: Found test patch of length {len(test_patch)}")
                        else:
                            if verbose:
                                print(f"Line {line_num}: No test patch found in git_patch")
                        
                        # Replace the git_patch with the test_patch
                        data['test_result']['git_patch'] = test_patch
                    else:
                        if verbose:
                            print(f"Line {line_num}: git_patch is empty")
                
                # Write the modified (or original) line to the output file
                f_out.write(json.dumps(data) + '\n')
                
            except json.JSONDecodeError as e:
                if verbose:
                    print(f"Line {line_num}: JSON decode error: {e}")
                # If the line is not valid JSON, write it as is
                f_out.write(line)
    
    # Print statistics
    print(f"Processed {input_path} -> {output_path}")
    print(f"Total lines: {total_lines}")
    print(f"Valid JSON lines: {processed_lines}")
    print(f"Lines with git_patch: {lines_with_patches}")
    print(f"Lines with test patches: {lines_with_test_patches}")


def main():
    parser = argparse.ArgumentParser(description="Process JSONL files to split git patches")
    parser.add_argument("input_path", help="Path to the input JSONL file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print verbose debugging information")
    
    args = parser.parse_args()
    process_jsonl_file(args.input_path, verbose=args.verbose)


if __name__ == "__main__":
    main()