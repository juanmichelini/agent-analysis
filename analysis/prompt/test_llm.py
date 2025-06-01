#!/usr/bin/env python3
"""
Simple script to test LLM API connection.
"""
import os
import sys
import toml
import litellm

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
    
    print(f"Testing LLM: {llm_name}")
    print(f"Model: {llm.get('model')}")
    print(f"API Key: {llm.get('api_key')[:5]}...{llm.get('api_key')[-5:]}")
    print(f"Base URL: {llm.get('base_url')}")
    
    # Set up environment variables
    os.environ["LITELLM_API_KEY"] = llm.get("api_key")
    os.environ["LITELLM_PROXY_URL"] = llm.get("base_url")
    
    # Test simple completion
    try:
        print("\nTesting completion...")
        response = litellm.completion(
            model=llm.get("model"),
            messages=[{"role": "user", "content": "Say hello world"}],
            api_base=llm.get("base_url"),
            api_key=llm.get("api_key"),
            timeout=10  # 10 seconds timeout
        )
        print(f"Response: {response.choices[0].message.content}")
        print("Test successful!")
    except Exception as e:
        print(f"Error: {e}")
        print("Test failed.")

if __name__ == "__main__":
    main()