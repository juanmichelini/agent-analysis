"""
Patch splitter module to separate a git patch into fix and test patches.
"""
from typing import Tuple, Dict, Optional


def split_patch(patch: str) -> Tuple[str, str]:
    """
    Split a git patch into two patches: one for the fix and one for the unit tests.
    
    Args:
        patch (str): The original git patch
        
    Returns:
        Tuple[str, str]: A tuple containing (fix_patch, test_patch)
    """
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
        file_header_lines = file_change.splitlines()
        for line in file_header_lines:
            if line.startswith('diff --git '):
                # Check if the file path contains 'test' or 'tests'
                if '/test/' in line or '/tests/' in line or '_test.' in line or line.endswith('_test'):
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