#!/usr/bin/env python3
"""
Simple script to test prompt evaluation with a single example.
"""
import os
import sys
import json
import toml
import litellm
import datetime

def main():
    # Read config
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.toml")
    try:
        config = toml.load(config_path)
    except Exception as e:
        print(f"Error reading config: {e}")
        sys.exit(1)
    
    # Get LLM config
    llm_config = config.get("llm", {})
    if not llm_config:
        print("Error: LLM configuration not found in config.toml")
        sys.exit(1)
    
    # Get the first LLM config
    llm_name = next(iter(llm_config.keys()))
    llm = llm_config[llm_name]
    model = llm.get("model")
    
    # Set up environment variables
    os.environ["LITELLM_API_KEY"] = llm.get("api_key")
    os.environ["LITELLM_PROXY_URL"] = llm.get("base_url")
    
    # Read initial prompt
    initial_prompt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "initial_prompt.txt")
    with open(initial_prompt_path, 'r') as f:
        initial_prompt = f.read().strip()
    
    # Read test dataset
    dataset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test", "test_dataset.jsonl")
    with open(dataset_path, 'r') as f:
        dataset = [json.loads(line.strip()) for line in f]
    
    # Get first item from dataset
    item = dataset[0]
    instance_id = item.get("instance_id", "")
    input_text = item.get("input", "")
    expected_output = item.get("expected_output", "")
    
    print(f"Testing with instance: {instance_id}")
    
    # Create experiment directory
    exp_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    exp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluation", exp_name)
    os.makedirs(exp_dir, exist_ok=True)
    
    # Save initial prompt
    with open(os.path.join(exp_dir, "prompt0.txt"), 'w') as f:
        f.write(initial_prompt)
    
    # Call LLM with initial prompt
    full_prompt = f"{initial_prompt}\n\n{input_text}"
    
    try:
        print("Calling LLM with initial prompt...")
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": full_prompt}],
            api_base=llm.get("base_url"),
            api_key=llm.get("api_key"),
            timeout=30  # 30 seconds timeout
        )
        actual_output = response.choices[0].message.content
        
        # Save actual output
        with open(os.path.join(exp_dir, "output0.txt"), 'w') as f:
            f.write(actual_output)
        
        print("Successfully generated output!")
        print(f"Results saved to {exp_dir}")
    except Exception as e:
        print(f"Error calling LLM: {e}")
        with open(os.path.join(exp_dir, "error.txt"), 'w') as f:
            f.write(f"Error: {str(e)}")

if __name__ == "__main__":
    main()