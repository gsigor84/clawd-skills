#!/usr/bin/env python3
"""
pipeline_report.py - Generate pipeline report from skill-forge run artifacts.

Usage:
    python pipeline_report.py --skill-name <name> [--mode notebooklm|web-research] [--notebook-url <url>]

Outputs:
    ~/clawd/tmp/skill-forge/<skill-name>/pipeline-report.md
"""

import argparse
import os
import sys
import json
from datetime import datetime

# Base paths
BASE_DIR = os.path.expanduser("~/clawd")
TMP_BASE = os.path.join(BASE_DIR, "tmp", "skill-forge")
SKILLS_DIR = os.path.join(BASE_DIR, "skills")
DEFAULT_PROMPTS_DIR = os.path.join(BASE_DIR, "tmp", "notebooklm-prompts")


def resolve_prompts_dir(skill_dir: str, task_state):
    """Resolve prompts directory in priority order:
    1) task-state.json promptsDir
    2) ~/clawd/tmp/skill-forge/<skill-name>/prompts/
    3) default ~/clawd/tmp/notebooklm-prompts/
    """
    if isinstance(task_state, dict):
        pd = (task_state.get("promptsDir") or "").strip()
        if pd and os.path.isdir(os.path.expanduser(pd)):
            return os.path.expanduser(pd)

    skill_prompts = os.path.join(skill_dir, "prompts")
    if os.path.isdir(skill_prompts):
        return skill_prompts

    return DEFAULT_PROMPTS_DIR


def read_file(path):
    """Read file content safely."""
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def list_prompts(prompts_dir):
    """List all prompt files in order."""
    prompts = {}
    for i in range(1, 18):
        filename = f"p{i:02d}.txt"
        path = os.path.join(prompts_dir, filename)
        content = read_file(path)
        if content:
            prompts[filename] = content
    return prompts


def list_responses(pass_dir):
    """List all response files in order."""
    responses = {}
    
    if not os.path.isdir(pass_dir):
        return responses
    
    # Method 1: Look for p01.response.txt...p17.response.txt (simple format)
    for i in range(1, 18):
        filename = f"p{i:02d}.response.txt"
        path = os.path.join(pass_dir, filename)
        content = read_file(path)
        if content:
            responses[f"p{i:02d}"] = content
    
    # Method 2: Look for *response.txt files (NotebookLM format with timestamps)
    if not responses:
        import glob
        response_files = glob.glob(os.path.join(pass_dir, "*response.txt"))
        # Sort by creation time
        response_files.sort(key=lambda x: os.path.getmtime(x))
        for path in response_files:
            content = read_file(path)
            if content:
                # Extract prompt number from filename
                basename = os.path.basename(path)
                # Try to extract prompt number
                if "prompt-01" in basename or "_01_" in basename:
                    responses["p01"] = content
                elif "prompt-02" in basename or "_02_" in basename:
                    responses["p02"] = content
                elif "prompt-03" in basename or "_03_" in basename:
                    responses["p03"] = content
                elif "prompt-04" in basename or "_04_" in basename:
                    responses["p04"] = content
                elif "prompt-05" in basename or "_05_" in basename:
                    responses["p05"] = content
                elif "prompt-06" in basename or "_06_" in basename:
                    responses["p06"] = content
                elif "prompt-07" in basename or "_07_" in basename:
                    responses["p07"] = content
                elif "prompt-08" in basename or "_08_" in basename:
                    responses["p08"] = content
                elif "prompt-09" in basename or "_09_" in basename:
                    responses["p09"] = content
                elif "prompt-10" in basename or "_10_" in basename:
                    responses["p10"] = content
                elif "prompt-11" in basename or "_11_" in basename:
                    responses["p11"] = content
                elif "prompt-12" in basename or "_12_" in basename:
                    responses["p12"] = content
                elif "prompt-13" in basename or "_13_" in basename:
                    responses["p13"] = content
                elif "prompt-14" in basename or "_14_" in basename:
                    responses["p14"] = content
                elif "prompt-15" in basename or "_15_" in basename:
                    responses["p15"] = content
                elif "prompt-16" in basename or "_16_" in basename:
                    responses["p16"] = content
                elif "prompt-17" in basename or "_17_" in basename:
                    responses["p17"] = content
    
    return responses


def list_gap_prompts(gaps_dir):
    """List all gap prompt files (p01.txt...p08.txt)."""
    gap_prompts = {}
    for i in range(1, 9):
        filename = f"p{i:02d}.txt"
        path = os.path.join(gaps_dir, filename)
        content = read_file(path)
        if content:
            gap_prompts[filename] = content
    return gap_prompts


def get_task_state(skill_dir):
    """Read task-state.json."""
    task_state_path = os.path.join(skill_dir, "task-state.json")
    content = read_file(task_state_path)
    if content:
        try:
            return json.loads(content)
        except:
            return content
    return None


def generate_report(skill_name, mode="notebooklm", notebook_url=""):
    """Generate the full pipeline report."""
    skill_dir = os.path.join(TMP_BASE, skill_name)
    
    if not os.path.isdir(skill_dir):
        print(f"Error: Skill directory not found: {skill_dir}", file=sys.stderr)
        sys.exit(1)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines = []
    lines.append(f"# Pipeline Report: {skill_name}")
    lines.append(f"Generated: {timestamp}")
    lines.append(f"Mode: {mode}")
    if notebook_url:
        lines.append(f"Notebook URL: {notebook_url}")
    lines.append("")
    
    # Get task state
    task_state = get_task_state(skill_dir)
    
    # ===========================================
    # PHASE 1: Baseline Extraction
    # ===========================================
    lines.append("## Phase 1 — Baseline Extraction")
    lines.append("")
    
    pass1_dir = os.path.join(skill_dir, "pass1")
    
    # Look in research-to-skill directory for pass1
    research_pass1 = os.path.join(BASE_DIR, "tmp", "research-to-skill", skill_name, "pass1")
    if os.path.isdir(research_pass1):
        pass1_dir = research_pass1
    
    prompts_dir = resolve_prompts_dir(skill_dir, task_state)
    prompts = list_prompts(prompts_dir)
    responses = list_responses(pass1_dir)
    
    lines.append("### Prompts sent:")
    for i in range(1, 18):
        filename = f"p{i:02d}.txt"
        content = prompts.get(filename, None)
        if content:
            first_line = content.split("\n")[0]
            lines.append(f"- **{filename}**: {first_line}")
    lines.append("")
    
    lines.append("### Responses received:")
    for i in range(1, 18):
        key = f"p{i:02d}"
        content = responses.get(key, None)
        status = "PASS" if content else "FAIL"
        lines.append(f"#### p{i:02d}.response.txt [{status}]")
        if content:
            lines.append("```")
            if len(content) > 5000:
                lines.append(content[:5000])
                lines.append(f"... [truncated, total {len(content)} chars]")
            else:
                lines.append(content)
            lines.append("```")
        else:
            lines.append("*No response file found*")
        lines.append("")
    
    # ===========================================
    # PHASE 2: Gap Analysis
    # ===========================================
    lines.append("## Phase 2 — Gap Analysis")
    lines.append("")
    
    gaps_dir = os.path.join(skill_dir, "gaps")
    
    # Look in research-to-skill directory for gaps
    research_gaps = os.path.join(BASE_DIR, "tmp", "research-to-skill", skill_name, "gaps")
    if os.path.isdir(research_gaps):
        gaps_dir = research_gaps
    
    # gap-prompts.md
    gap_prompts_md = read_file(os.path.join(gaps_dir, "gap-prompts.md"))
    lines.append("### gap-prompts.md:")
    lines.append("```")
    if gap_prompts_md:
        if len(gap_prompts_md) > 10000:
            lines.append(gap_prompts_md[:10000])
            lines.append(f"... [truncated, total {len(gap_prompts_md)} chars]")
        else:
            lines.append(gap_prompts_md)
    else:
        lines.append("*No gap-prompts.md found*")
    lines.append("```")
    lines.append("")
    
    # gap-rules.md
    gap_rules_md = read_file(os.path.join(gaps_dir, "gap-rules.md"))
    lines.append("### gap-rules.md:")
    lines.append("```")
    if gap_rules_md:
        if len(gap_rules_md) > 10000:
            lines.append(gap_rules_md[:10000])
            lines.append(f"... [truncated, total {len(gap_rules_md)} chars]")
        else:
            lines.append(gap_rules_md)
    else:
        lines.append("*No gap-rules.md found*")
    lines.append("```")
    lines.append("")
    
    # Gap prompt files (p01.txt...p08.txt)
    gap_prompts_files = list_gap_prompts(gaps_dir)
    lines.append("### Gap prompt files:")
    for i in range(1, 9):
        filename = f"p{i:02d}.txt"
        content = gap_prompts_files.get(filename, None)
        status = "PASS" if content else "MISSING"
        lines.append(f"#### {filename} [{status}]")
        if content:
            lines.append("```")
            lines.append(content)
            lines.append("```")
        lines.append("")
    
    # Task state for entity counts
    if task_state and isinstance(task_state, dict):
        lines.append("### Task state info:")
        lines.append("```")
        lines.append(json.dumps(task_state, indent=2))
        lines.append("```")
    lines.append("")
    
    # ===========================================
    # PHASE 3: Deep Extraction
    # ===========================================
    lines.append("## Phase 3 — Deep Extraction")
    lines.append("")
    
    pass2_dir = os.path.join(skill_dir, "pass2")
    
    # Look in research-to-skill directory for pass2
    research_pass2 = os.path.join(BASE_DIR, "tmp", "research-to-skill", skill_name, "pass2")
    if os.path.isdir(research_pass2):
        pass2_dir = research_pass2
    
    pass2_responses = list_responses(pass2_dir)
    
    for i in range(1, 18):
        key = f"p{i:02d}"
        content = pass2_responses.get(key, None)
        status = "PASS" if content else "FAIL"
        lines.append(f"### p{i:02d}.response.txt [{status}]")
        if content:
            lines.append("```")
            if len(content) > 5000:
                lines.append(content[:5000])
                lines.append(f"... [truncated, total {len(content)} chars]")
            else:
                lines.append(content)
            lines.append("```")
        else:
            lines.append("*No response file found*")
        lines.append("")
    
    # ===========================================
    # PHASE 4: Synthesis
    # ===========================================
    lines.append("## Phase 4 — Synthesis")
    lines.append("")
    
    synthesis_dir = os.path.join(skill_dir, "synthesis")
    
    # Look in research-to-skill directory for synthesis
    research_synthesis = os.path.join(BASE_DIR, "tmp", "research-to-skill", skill_name, "synthesis")
    if os.path.isdir(research_synthesis):
        synthesis_dir = research_synthesis
    
    # enriched-summary.md
    enriched_summary = read_file(os.path.join(synthesis_dir, "enriched-summary.md"))
    lines.append("### enriched-summary.md:")
    if enriched_summary:
        size = len(enriched_summary)
        lines.append(f"Size: {size} characters")
        lines.append("```")
        if len(enriched_summary) > 15000:
            lines.append(enriched_summary[:15000])
            lines.append(f"... [truncated, total {size} chars]")
        else:
            lines.append(enriched_summary)
        lines.append("```")
    else:
        lines.append("*No enriched-summary.md found*")
    lines.append("")
    
    # gap-rules.md in synthesis
    synthesis_gap_rules = read_file(os.path.join(synthesis_dir, "gap-rules.md"))
    lines.append("### synthesis/gap-rules.md:")
    if synthesis_gap_rules:
        size = len(synthesis_gap_rules)
        lines.append(f"Size: {size} characters")
        lines.append("```")
        if len(synthesis_gap_rules) > 5000:
            lines.append(synthesis_gap_rules[:5000])
            lines.append(f"... [truncated, total {size} chars]")
        else:
            lines.append(synthesis_gap_rules)
        lines.append("```")
    else:
        lines.append("*No synthesis/gap-rules.md found*")
    lines.append("")
    
    # ===========================================
    # PHASE 4.5: Creative Expansion
    # ===========================================
    creative_expansion = read_file(os.path.join(skill_dir, "creative-expansion.md"))
    if creative_expansion:
        lines.append("## Phase 4.5 — Creative Expansion")
        lines.append("")
        lines.append("### creative-expansion.md:")
        lines.append("```")
        if len(creative_expansion) > 10000:
            lines.append(creative_expansion[:10000])
            lines.append(f"... [truncated, total {len(creative_expansion)} chars]")
        else:
            lines.append(creative_expansion)
        lines.append("```")
        lines.append("")
    
    # ===========================================
    # PHASE 5: Skill Build
    # ===========================================
    lines.append("## Phase 5 — Skill Build")
    lines.append("")
    
    skill_md_path = os.path.join(SKILLS_DIR, skill_name, "SKILL.md")
    skill_md = read_file(skill_md_path)
    
    lines.append("### Final SKILL.md:")
    if skill_md:
        lines.append(f"Location: {skill_md_path}")
        lines.append(f"Size: {len(skill_md)} characters")
        lines.append("```")
        if len(skill_md) > 15000:
            lines.append(skill_md[:15000])
            lines.append(f"... [truncated, total {len(skill_md)} chars]")
        else:
            lines.append(skill_md)
        lines.append("```")
    else:
        lines.append("*No SKILL.md found*")
    lines.append("")
    
    # Validator results
    validator_script = os.path.join(BASE_DIR, "skills", "skillmd-builder-agent", "scripts", "validate_skillmd.py")
    if os.path.isfile(validator_script) and skill_md:
        lines.append("### Validator check:")
        lines.append(f"*Run: /opt/anaconda3/bin/python3 {validator_script} {skill_md_path}*")
        lines.append("*Results: (run command manually to see output)*")
        lines.append("")
    
    # ===========================================
    # PHASE 6: Critic
    # ===========================================
    lines.append("## Phase 6 — Critic")
    lines.append("")
    
    if task_state:
        lines.append("### Task state (critic results):")
        lines.append("```")
        if isinstance(task_state, dict):
            # Pretty print the phases section
            phases = task_state.get("phases", {})
            for phase_name, phase_data in phases.items():
                lines.append(f"**{phase_name}**: {phase_data.get('status', 'N/A')}")
            lines.append("")
            if task_state.get("failures"):
                lines.append("Failures:")
                for f in task_state.get("failures", []):
                    lines.append(f"  - {f}")
        else:
            lines.append(str(task_state)[:2000])
        lines.append("```")
    else:
        lines.append("*No task state found*")
    lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate skill-forge pipeline report")
    parser.add_argument("--skill-name", required=True, help="Skill name (folder name)")
    parser.add_argument("--mode", choices=["notebooklm", "web-research"], default="notebooklm", help="Pipeline mode")
    parser.add_argument("--notebook-url", default="", help="NotebookLM URL (if applicable)")
    
    args = parser.parse_args()
    
    report = generate_report(args.skill_name, args.mode, args.notebook_url)
    
    # Write report
    output_path = os.path.join(TMP_BASE, args.skill_name, "pipeline-report.md")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    # Report stats
    size = os.path.getsize(output_path)
    print(f"Report written to: {output_path}")
    print(f"File size: {size} bytes")
    
    # Print first 50 lines
    with open(output_path, "r") as f:
        lines = f.readlines()
        print("\n--- First 50 lines ---")
        for line in lines[:50]:
            print(line.rstrip())


if __name__ == "__main__":
    main()