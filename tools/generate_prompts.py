#!/usr/bin/env python3
"""
generate_prompts.py - Generate 17 topic-specific research prompts for NotebookLM.

Usage:
    python generate_prompts.py --topic "creative practice" --goal "help me apply X to Y" --output-dir ./prompts

Outputs:
    p01.txt ... p17.txt - 17 tailored research prompts
"""

import argparse
import os
import sys
import json

# Try to use openai SDK, fall back to requests
try:
    from openai import OpenAI
    USE_OPENAI_SDK = True
except ImportError:
    USE_OPENAI_SDK = False
    import urllib.request
    import urllib.parse


DEFAULT_SYSTEM_MSG = """You are a research prompt engineer designing questions for NotebookLM — a tool that answers questions based ONLY on uploaded source documents. Your prompts must be questions that will extract actionable knowledge FROM THE SOURCES, not general knowledge about the topic.

Each prompt must:
- Ask NotebookLM to find specific techniques, frameworks, or methods FROM THE UPLOADED SOURCES
- Reference 'the sources' or 'the authors' or 'the books' so NotebookLM knows to look in its documents
- Extract HOW TO APPLY the knowledge, not just WHAT IT IS
- Be tailored to the goal: {goal}
- Be about the topic: {topic}

Bad example: 'How to use mind mapping to brainstorm video concepts'
Good example: 'From the uploaded sources, what specific techniques do the authors recommend for generating ideas when you are stuck on a creative task? How would you apply each technique to a real project right now?'

Generate 17 prompts. Return only the prompts numbered 1-17."""


class OpenAIAPIClient:
    """Simple OpenAI API client using requests."""
    
    def __init__(self, api_key, model="gpt-4o-mini"):
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


def generate_prompts(topic, goal, model="gpt-4o-mini"):
    """Generate 17 prompts using OpenAI."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    system_msg = DEFAULT_SYSTEM_MSG.format(topic=topic, goal=goal)
    
    user_msg = f"""Generate 17 research prompts for a NotebookLM notebook.

Topic: {topic}
Goal: {goal}

Each prompt should:
- Be completely tailored to the topic and goal
- Extract actionable techniques, not theoretical summaries
- Ask "how to apply" not "what does this say"
- Work for the specific domain
- Never mention AI platforms, SKILL.md, OpenClaw, or agent loops

Return ONLY the 17 prompts numbered 1-17, nothing else. Each prompt should be 2-5 sentences."""

    if USE_OPENAI_SDK:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ]
        )
        return response.choices[0].message.content
    else:
        client = OpenAIAPIClient(api_key, model)
        return client.chat([
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ])


def parse_prompts(prompts_text):
    """Parse the numbered prompts from the model output."""
    prompts = {}
    lines = prompts_text.strip().split("\n")
    current_num = None
    current_text = []
    
    for line in lines:
        line = line.strip()
        # Check for numbered prompt (1., 2., etc.)
        if line and line[0].isdigit() and "." in line:
            # Save previous prompt
            if current_num is not None and current_text:
                prompts[f"{current_num:02d}"] = " ".join(current_text)
            
            # Parse new prompt number
            parts = line.split(".", 1)
            try:
                current_num = int(parts[0].strip())
                current_text = [parts[1].strip()] if len(parts) > 1 else []
            except:
                # Not a valid prompt number, might be continuation
                if current_num is not None:
                    current_text.append(line)
        elif current_num is not None:
            # Continuation of previous prompt
            current_text.append(line)
    
    # Save last prompt
    if current_num is not None and current_text:
        prompts[f"{current_num:02d}"] = " ".join(current_text)
    
    return prompts


def main():
    parser = argparse.ArgumentParser(description="Generate 17 topic-specific research prompts")
    parser.add_argument("--topic", required=True, help="Topic of the notebook")
    parser.add_argument("--goal", required=True, help="What the skill should DO for the user")
    parser.add_argument("--output-dir", required=True, help="Output directory for prompts")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model to use")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Generating prompts for topic: {args.topic}")
    print(f"Goal: {args.goal}")
    
    # Generate prompts
    prompts_text = generate_prompts(args.topic, args.goal, args.model)
    
    # Parse prompts
    prompts = parse_prompts(prompts_text)
    
    print(f"\nGenerated {len(prompts)} prompts:")
    
    # Write prompts to files
    for num in range(1, 18):
        filename = f"p{num:02d}.txt"
        filepath = os.path.join(args.output_dir, filename)
        content = prompts.get(f"{num:02d}", "")
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"  {filename}: {content[:60]}..." if len(content) > 60 else f"  {filename}: {content}")
    
    print(f"\nPrompts saved to: {args.output_dir}")


if __name__ == "__main__":
    main()