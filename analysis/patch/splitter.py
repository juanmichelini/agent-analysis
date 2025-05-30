"""
Patch splitter module to separate a git patch into fix and test patches.
"""
import re
from typing import Tuple, Dict, Optional, List


def is_test_file(file_path: str) -> bool:
    """
    Determine if a file path is likely a test file.
    
    Args:
        file_path (str): The file path to check
        
    Returns:
        bool: True if the file is likely a test file, False otherwise
    """
    test_indicators = [
        '/test/', '/tests/', 
        '_test.', 'test_', 
        '/spec/', '_spec.',
        '/unittest/', '/unit_test/',
        'Test.java', 'Tests.java',
        'test.js', 'spec.js',
        'test.py', 'test.rb',
        'test.go', 'test.ts'
    ]
    
    for indicator in test_indicators:
        if indicator in file_path:
            return True
    
    # Check if the file ends with common test file patterns
    if re.search(r'(^|/)test_[^/]+$', file_path) or re.search(r'(^|/)[^/]+_test$', file_path):
        return True
        
    return False


def split_patch(patch: str) -> Tuple[str, str]:
    """
    Split a git patch into two patches: one for the fix and one for the unit tests.
    
    Args:
        patch (str): The original git patch
        
    Returns:
        Tuple[str, str]: A tuple containing (fix_patch, test_patch)
    """
    if not patch or not patch.strip():
        return "", ""
        
    # Initialize empty patches
    fix_patch = []
    test_patch = []
    
    # Split the patch into individual file changes
    file_changes = []
    current_file_change = []
    
    for line in patch.splitlines(True):  # Keep line endings
        if line.startswith('diff --git '):
            if current_file_change:
                file_changes.append(''.join(current_file_change))
                current_file_change = []
        current_file_change.append(line)
    
    if current_file_change:
        file_changes.append(''.join(current_file_change))
    
    # Categorize each file change as either a fix or a test
    for file_change in file_changes:
        # Check if this is a test file
        is_test = False
        file_paths = []
        
        file_header_lines = file_change.splitlines()
        for line in file_header_lines:
            if line.startswith('diff --git '):
                # Extract file paths from the diff line
                match = re.match(r'diff --git a/(.*) b/(.*)', line)
                if match:
                    file_paths.extend([match.group(1), match.group(2)])
                else:
                    # Try alternative format
                    match = re.match(r'diff --git (.*) (.*)', line)
                    if match:
                        file_paths.extend([match.group(1), match.group(2)])
        
        # Check if any of the file paths indicate a test file
        for path in file_paths:
            if is_test_file(path):
                is_test = True
                break
        
        # Add to the appropriate patch
        if is_test:
            test_patch.append(file_change)
        else:
            fix_patch.append(file_change)
    
    # Join the patches
    fix_patch_str = ''.join(fix_patch)
    test_patch_str = ''.join(test_patch)
    
    return fix_patch_str, test_patch_str