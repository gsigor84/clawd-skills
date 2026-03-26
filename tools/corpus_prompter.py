#!/usr/bin/env python3
"""
corpus_prompter.py - Run prompts against a text corpus using OpenAI API.

Usage:
    python corpus_prompter.py \
        --corpus-file ./research-corpus.md \
        --prompts-dir ~/clawd/tmp/notebooklm-prompts \
        --output-dir ./output \
        --model gpt-4o-mini

Outputs:
    p01.txt, p02.txt, ... p17.txt in output-dir (each containing the model's response)
"""

import argparse
import os
import sys
import glob
from datetime import datetime

# Try to import openai, fall back to requests if not available
try:
    from openai import OpenAI
    USE_OPENAI_SDK = True
except ImportError:
    USE_OPENAI_SDK = False
    import json
    import urllib.request


class OpenAIAPIClient:
    """Simple OpenAI API client using requests (no SDK dependency)."""
    
    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"
    
    def chat(self, messages):
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7
        }
        
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            raise Exception(f"API call failed: {e}")


def load_corpus(corpus_file):
    """Load the corpus file content."""
    with open(corpus_file, "r", encoding="utf-8") as f:
        return f.read()


def load_prompts(prompts_dir):
    """Load all prompt files from the prompts directory."""
    # Find all p*.txt files and sort them numerically
    prompt_files = sorted(glob.glob(os.path.join(prompts_dir, "p*.txt")), 
                          key=lambda x: int(os.path.basename(x)[1:-4].lstrip('0') or 0))
    
    prompts = {}
    for path in prompt_files:
        name = os.path.basename(path)
        with open(path, "r", encoding="utf-8") as f:
            prompts[name] = f.read()
    
    return prompts


def run_prompts(corpus_content, prompts, output_dir, model):
    """Run each prompt against the corpus and save responses."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Initialize client
    if USE_OPENAI_SDK:
        client = OpenAI(api_key=api_key)
    else:
        client = OpenAIAPIClient(api_key, model)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    
    for prompt_name, prompt_text in prompts.items():
        print(f"Running {prompt_name}...")
        
        # Build the message with context
        system_msg = "You are a research assistant. Answer the user's question based ONLY on the provided research corpus. If the corpus doesn't contain enough information to answer, say so."
        user_msg = f"RESEARCH CORPUS:\n\n{corpus_content}\n\n---\n\nQUESTION:\n{prompt_text}"
        
        try:
            if USE_OPENAI_SDK:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg}
                    ]
                )
                answer = response.choices[0].message.content
            else:
                answer = client.chat([
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ])
            
            # Save response
            output_path = os.path.join(output_dir, prompt_name.replace(".txt", ".response.txt"))
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(answer)
            
            results[prompt_name] = "OK"
            print(f"  → {output_path}")
            
        except Exception as e:
            results[prompt_name] = f"FAILED: {e}"
            print(f"  → FAILED: {e}", file=sys.stderr)
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Run prompts against a text corpus using OpenAI")
    parser.add_argument("--corpus-file", required=True, help="Path to the corpus markdown file")
    parser.add_argument("--prompts-dir", required=True, help="Directory containing p01.txt...p17.txt prompts")
    parser.add_argument("--output-dir", required=True, help="Output directory for responses")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model to use (default: gpt-4o-mini)")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.isfile(args.corpus_file):
        print(f"Error: Corpus file not found: {args.corpus_file}", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isdir(args.prompts_dir):
        print(f"Error: Prompts directory not found: {args.prompts_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Check API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)
    
    # Load corpus
    print(f"Loading corpus: {args.corpus_file}")
    corpus_content = load_corpus(args.corpus_file)
    print(f"  Corpus size: {len(corpus_content)} chars")
    
    # Load prompts
    print(f"Loading prompts: {args.prompts_dir}")
    prompts = load_prompts(args.prompts_dir)
    print(f"  Found {len(prompts)} prompts")
    
    # Run prompts
    print(f"\nRunning prompts with {args.model}...")
    results = run_prompts(corpus_content, prompts, args.output_dir, args.model)
    
    # Summary
    print("\n--- Summary ---")
    ok_count = sum(1 for v in results.values() if v == "OK")
    print(f"Completed: {ok_count}/{len(results)}")
    
    for name, status in results.items():
        if status != "OK":
            print(f"  {name}: {status}")
    
    if ok_count == len(results):
        print("\nDone.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()