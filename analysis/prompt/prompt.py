#!/usr/bin/env python3
"""
Script to evaluate and improve prompts based on test data.
"""
import argparse
import json
import os
import sys
import toml
import glob
import datetime
import litellm
from typing import Dict, List, Any

def setup_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Prompt evaluation tool")
    parser.add_argument("--initial_prompt", required=True, help="Path to a txt file containing the initial prompt")
    parser.add_argument("--dataset", required=True, help="Path to a jsonl file with test data")
    parser.add_argument("--resume", action="store_true", help="Resume from existing experiment")
    parser.add_argument("--max_items", type=int, default=float('inf'), help="Maximum number of items to process")
    parser.add_argument("--start_index", type=int, default=0, help="Index of the first item to process (0-based)")
    return parser.parse_args()

def read_config() -> Dict[str, Any]:
    """Read the configuration file."""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.toml")
    try:
        return toml.load(config_path)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading configuration: {e}")
        sys.exit(1)

def read_prompt(prompt_path: str) -> str:
    """Read the prompt from a file."""
    try:
        with open(prompt_path, 'r') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading prompt file: {e}")
        sys.exit(1)

def read_dataset(dataset_path: str) -> List[Dict[str, str]]:
    """Read the dataset from a JSONL file."""
    data = []
    try:
        with open(dataset_path, 'r') as f:
            for line in f:
                data.append(json.loads(line.strip()))
        return data
    except Exception as e:
        print(f"Error reading dataset: {e}")
        sys.exit(1)

def setup_llm(llm_config: Dict[str, Any]) -> None:
    """Configure litellm with the provided configuration."""
    if not llm_config:
        print("Error: LLM configuration not found in config.toml")
        sys.exit(1)
    
    # Get the first LLM config (assuming there's only one)
    llm_name = next(iter(llm_config.keys()))
    config = llm_config[llm_name]
    
    # Set up litellm
    os.environ["LITELLM_API_KEY"] = config.get("api_key")
    if config.get("base_url"):
        os.environ["LITELLM_PROXY_URL"] = config.get("base_url")

def get_exp_name() -> str:
    """Get the experiment name from environment or generate a timestamp-based one."""
    exp_name = os.environ.get("EXP_NAME")
    if not exp_name:
        exp_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return exp_name

def create_exp_directory(exp_name: str, resume: bool = False) -> str:
    """Create the experiment directory."""
    exp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluation", exp_name)
    if os.path.exists(exp_dir) and not resume:
        print(f"Error: Experiment directory {exp_dir} already exists. Use --resume to continue.")
        sys.exit(1)
    
    os.makedirs(exp_dir, exist_ok=True)
    return exp_dir

def call_llm(model: str, prompt: str, timeout: int = 30, max_retries: int = 3) -> str:
    """Call the LLM with the given prompt with improved retry logic and timeout handling."""
    current_timeout = timeout
    for attempt in range(max_retries + 1):
        try:
            print(f"Calling LLM with timeout {current_timeout} seconds... (Attempt {attempt + 1}/{max_retries + 1})")
            response = litellm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                api_base=os.environ.get("LITELLM_PROXY_URL"),
                api_key=os.environ.get("LITELLM_API_KEY"),
                timeout=current_timeout,
                max_tokens=1024,  # Limit response size to avoid timeouts
                temperature=0.2   # Lower temperature for more deterministic responses
            )
            print("LLM call successful!")
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling LLM (Attempt {attempt + 1}/{max_retries + 1}): {e}")
            if attempt < max_retries:
                print(f"Retrying in 3 seconds...")
                import time
                time.sleep(3)
                # Reduce the timeout slightly for subsequent attempts
                current_timeout = max(15, current_timeout - 5)
            else:
                return f"Error: {str(e)}"

def generate_improved_prompt(model: str, initial_prompt: str, input_text: str, 
                            expected_output: str, actual_output: str) -> str:
    """Generate an improved prompt based on the results."""
    prompt = f"""
I need to improve a prompt for a language model. Here's the current situation:

INITIAL PROMPT:
{initial_prompt}

INPUT:
{input_text}

EXPECTED OUTPUT:
{expected_output}

ACTUAL OUTPUT:
{actual_output}

Based on the difference between the expected and actual outputs, please suggest an improved version of the initial prompt.
Make minimal general changes. The prompt will be run in many different repositories, so don't mention anything too specific.

IMPROVED PROMPT:
"""
    # Use a shorter timeout (30 seconds) for this task to avoid hanging
    return call_llm(model, prompt, timeout=30)

def generate_composite_prompt(model: str, initial_prompt: str, improved_prompts: List[Dict[str, str]]) -> str:
    """Generate a composite prompt that works well for all cases."""
    prompt = f"""
I need to create a composite prompt that works well for multiple cases. Here's the initial prompt:

INITIAL PROMPT:
{initial_prompt}

Here are the improved prompts for specific cases:

"""
    
    for i, item in enumerate(improved_prompts):
        prompt += f"""
CASE {i+1}:
INPUT: {item['input']}
IMPROVED PROMPT: {item['new_prompt']}

"""
    
    prompt += """
Based on the initial prompt and the improved prompts for specific cases, please create a new composite prompt that would work well for all these cases and similar ones. The composite prompt should be general enough to handle various inputs but specific enough to produce outputs similar to the expected ones.
Make minimal changes to the intial prompt to consider the improvements of the new prompts.

Only give the composite prompt, do not give 
COMPOSITE PROMPT:
"""
    
    # Use a shorter timeout (45 seconds) for this task to avoid hanging
    return call_llm(model, prompt, timeout=45)

def main():
    args = setup_args()
    config = read_config()
    selected_ids = config.get("selected_ids", [])
    
    # Set up LLM
    llm_config = config.get("llm", {})
    setup_llm(llm_config)
    model = next(iter(llm_config.values())).get("model")
    
    # Read initial prompt and dataset
    initial_prompt = read_prompt(args.initial_prompt)
    dataset = read_dataset(args.dataset)
    
    # Set up experiment
    exp_name = get_exp_name()
    exp_dir = create_exp_directory(exp_name, args.resume)
    
    # Save initial prompt
    with open(os.path.join(exp_dir, "prompt0.txt"), 'w') as f:
        f.write(initial_prompt)
    
    # Check if we need to resume from a previous run or start from a specific index
    resume_from = args.start_index
    progress_files = sorted(glob.glob(os.path.join(exp_dir, "progress_*.json")))
    
    if args.resume and progress_files:
        last_progress_file = progress_files[-1]
        resume_from = int(os.path.basename(last_progress_file).split("_")[1].split(".")[0]) + 1
        print(f"Resuming from item {resume_from}")
        
        # Load previous results
        results = []
        for i in range(resume_from):
            progress_file = os.path.join(exp_dir, f"progress_{i}.json")
            if os.path.exists(progress_file):
                with open(progress_file, 'r') as f:
                    results.append(json.load(f))
    else:
        if resume_from > 0:
            print(f"Starting from item {resume_from}")
        results = []
    
    count = resume_from
    max_items = args.max_items  # Use the max_items from command line arguments
    
    # Create a set of already processed instance IDs
    processed_ids = set()
    for i in range(resume_from):
        progress_file = os.path.join(exp_dir, f"progress_{i}.json")
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                processed_ids.add(json.load(f).get("instance_id", ""))
    
    # Process items starting from start_index
    for idx, item in enumerate(dataset):
        if count >= resume_from + max_items:
            break
            
        # Skip items before start_index
        if idx < resume_from:
            continue
            
        instance_id = item.get("instance_id", "")
        
        # Skip if already processed
        if instance_id in processed_ids:
            print(f"Skipping already processed item: {instance_id}")
            continue
            
        # Skip if not in selected_ids
        if selected_ids and instance_id not in selected_ids:
            continue
        
        input_text = item.get("input", "")
        expected_output = item.get("expected_output", "")
        
        print(f"Processing item {count+1-resume_from}/{max_items} (index {count}): {instance_id}")
        
        # Call LLM with initial prompt
        full_prompt = f"{initial_prompt}\n\n{input_text}"
        print("Calling LLM with timeout 30 seconds...")
        actual_output = call_llm(model, full_prompt, timeout=30)
        
        # Save intermediate result
        with open(os.path.join(exp_dir, f"output_{count}.txt"), 'w') as f:
            f.write(actual_output)
        
        # Generate improved prompt
        print(f"Generating improved prompt for {instance_id}")
        new_prompt_full = generate_improved_prompt(
            model, initial_prompt, input_text, expected_output, actual_output
        )
        
        # Extract only the improved prompt without LLM comments
        # Look for the IMPROVED PROMPT: marker and extract content until --- or end of text
        improved_prompt_only = ""
        if "**IMPROVED PROMPT:**" in new_prompt_full:
            # Extract content between **IMPROVED PROMPT:** and --- or end of text
            start_marker = "**IMPROVED PROMPT:**"
            end_markers = ["---", "The key improvement"]
            
            start_idx = new_prompt_full.find(start_marker) + len(start_marker)
            end_idx = float('inf')
            
            for marker in end_markers:
                marker_idx = new_prompt_full.find(marker, start_idx)
                if marker_idx != -1 and marker_idx < end_idx:
                    end_idx = marker_idx
            
            if end_idx == float('inf'):
                # No end marker found, use the rest of the text
                improved_prompt_only = new_prompt_full[start_idx:].strip()
            else:
                improved_prompt_only = new_prompt_full[start_idx:end_idx].strip()
        else:
            # Fallback if the expected format is not found
            improved_prompt_only = new_prompt_full
        
        # Save improved prompt (clean version)
        with open(os.path.join(exp_dir, f"prompt_{count+1}.txt"), 'w') as f:
            f.write(improved_prompt_only)
            
        # Save full response for debugging
        with open(os.path.join(exp_dir, f"prompt_{count+1}_full.txt"), 'w') as f:
            f.write(new_prompt_full)
        
        # Save result
        result = {
            "instance_id": instance_id,
            "input": input_text,
            "expected_output": expected_output,
            "actual_output": actual_output,
            "new_prompt": improved_prompt_only,
            "new_prompt_full": new_prompt_full
        }
        results.append(result)
        
        # Save progress after each item
        with open(os.path.join(exp_dir, f"progress_{count}.json"), 'w') as f:
            json.dump(result, f, indent=2)
            
        count += 1
    
    # Save results
    run_path = os.path.join(exp_dir, "run0.jsonl")
    with open(run_path, 'w') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')
    
    # Generate composite prompt if we have results
    if results:
        print("Generating composite prompt")
        composite_prompt = generate_composite_prompt(model, initial_prompt, results)
        
        # Save composite prompt
        with open(os.path.join(exp_dir, "prompt1.txt"), 'w') as f:
            f.write(composite_prompt)
    
    print(f"Experiment completed. Results saved to {exp_dir}")

if __name__ == "__main__":
    main()