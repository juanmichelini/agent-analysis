# Prompt Analysis System

This system allows you to evaluate and improve prompts based on test data from the SWE-bench_Verified dataset.

## Directory Structure

- `prompt/`: Main directory for the prompt analysis system
  - `prompt.py`: Main script for prompt evaluation and improvement
  - `initial_prompt.txt`: Initial prompt to be evaluated and improved
  - `config.toml`: Configuration file for LLM API access
  - `test_llm.py`: Script to test LLM API connection
  - `simple_test.py`: Script to run a simple test with a single example
  - `test/`: Directory containing test datasets
    - `get_test_data.py`: Script to fetch and process SWE-bench_Verified dataset
    - `test_dataset.jsonl`: Dataset for testing prompts
    - `fix_dataset.jsonl`: Dataset for fixing prompts
  - `evaluation/`: Directory containing evaluation results
    - Each subdirectory is a timestamp of when the evaluation was run
    - Contains prompt0.txt, prompt1.txt, and run0.jsonl files

## Setup

1. Make sure you have the required dependencies installed:
   ```bash
   pip install datasets litellm toml
   ```

2. Configure your LLM API access in `config.toml`:
   ```toml
   [llm.proxy-claude-3-7-sonnet-20250219]
   model = "litellm_proxy/anthropic/claude-3-7-sonnet-20250219"
   api_key = "your-api-key"
   base_url = "https://llm-proxy.app.all-hands.dev"
   ```

3. Create an initial prompt in `initial_prompt.txt`.

## Usage

### Generate Test Datasets

```bash
cd prompt
python test/get_test_data.py
```

This will generate `test_dataset.jsonl` and `fix_dataset.jsonl` in the `test/` directory.

### Test LLM API Connection

```bash
python test_llm.py
```

### Run a Simple Test

```bash
python simple_test.py
```

This will run a test with a single example from the test dataset.

### Run Full Prompt Evaluation

```bash
python prompt.py --initial_prompt initial_prompt.txt --dataset test/test_dataset.jsonl
```

This will:
1. Evaluate the initial prompt on the test dataset
2. Generate improved prompts for each example
3. Generate a composite prompt that works well for all examples
4. Save all results in the `evaluation/` directory

## Results

The evaluation results are saved in the `evaluation/` directory, with each run in a timestamped subdirectory:

- `prompt0.txt`: The initial prompt
- `prompt1.txt`: The improved composite prompt
- `run0.jsonl`: Detailed results for each example, including:
  - Input text
  - Expected output
  - Actual output
  - Improved prompt for that specific example

## Troubleshooting

If you encounter issues with the LLM API:
1. Check your API key and base URL in `config.toml`
2. Run `test_llm.py` to test the connection
3. Try increasing the timeout values in `prompt.py`