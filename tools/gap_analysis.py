#!/opt/anaconda3/bin/python3
"""Gap analysis script for research-to-skill pipeline.

Usage:
    python gap_analysis.py --input-dir /path/to/lightrag-responses --output-file gap-prompts.md

This script:
1. Feeds text files into LightRAG
2. Reads stored JSON entities/relations from rag_storage
3. Slices top layer (≥3 connections), recalculates graph
4. Finds clusters with NO relations between them
5. Generates bridging questions for each gap
6. Generates transcend-mode questions for 3 most isolated entities
7. Outputs gap-prompts.md and gap-rules.md
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple

# LightRAG imports
WORKING_DIR = "./rag_storage"
DEFAULT_PROMPTS_DIR = "/Users/igorsilva/clawd/tmp/notebooklm-prompts"


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Gap analysis for research-to-skill pipeline")
    ap.add_argument("--input-dir", required=True, help="Directory containing LightRAG response text files")
    ap.add_argument("--output-file", default="gap-prompts.md", help="Output file for gap prompts (default: gap-prompts.md)")
    ap.add_argument("--working-dir", default=WORKING_DIR, help="LightRAG working directory (default: ./rag_storage)")
    ap.add_argument("--llm-model", default="gpt-4o-mini", help="LLM model for LightRAG (default: gpt-4o-mini)")
    ap.add_argument("--embedding-model", default="text-embedding-3-small", help="Embedding model (default: text-embedding-3-small)")
    return ap.parse_args()


def setup_lightrag(working_dir: str) -> None:
    """Initialize LightRAG storage directory."""
    os.makedirs(working_dir, exist_ok=True)
    # Clear existing storage for fresh analysis
    storage_path = Path(working_dir) / "rag_storage"
    if storage_path.exists():
        shutil.rmtree(storage_path)


def insert_documents(input_dir: str, working_dir: str, llm_model: str, embedding_model: str) -> None:
    """Feed all text files into LightRAG.

    Preference rule:
    - If clean-summary.md exists alongside summary.md in input_dir, prefer clean-summary.md
      and ignore summary.md to avoid duplicate/dirty technique blocks.
    """
    input_path = Path(input_dir)

    # Prefer clean-summary.md over summary.md when both exist
    clean_summary = input_path / "clean-summary.md"
    summary = input_path / "summary.md"

    text_files = list(input_path.glob("*.txt")) + list(input_path.glob("*.md"))
    if clean_summary.exists():
        text_files = [p for p in text_files if p.name != "summary.md"]

    if not text_files:
        print(f"WARNING: No text files found in {input_dir}")
        return
    
    # Build Python script to insert documents
    insert_script = f'''
import asyncio
import os
from pathlib import Path
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
from lightrag.utils import setup_logger

setup_logger("lightrag", level="WARNING")

WORKING_DIR = "{working_dir}"

async def main():
    rag = LightRAG(
        working_dir=WORKING_DIR,
        embedding_func=openai_embed,
        llm_model_func=gpt_4o_mini_complete,
    )
    await rag.initialize_storages()
    
    # Insert all text files
    input_path = Path("{input_dir}")
    for f in input_path.glob("*.txt"):
        content = f.read_text(encoding="utf-8", errors="replace")
        await rag.ainsert(content)
        print(f"Inserted: {{f.name}}")
    for f in input_path.glob("*.md"):
        content = f.read_text(encoding="utf-8", errors="replace")
        await rag.ainsert(content)
        print(f"Inserted: {{f.name}}")
    
    await rag.finalize_storages()

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(insert_script)
        script_path = f.name
    
    try:
        result = subprocess.run(
            ["/opt/anaconda3/bin/python3", script_path],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            print(f"ERROR inserting documents: {result.stderr}")
            sys.exit(1)
        print(f"Inserted {len(text_files)} documents into LightRAG")
    finally:
        os.unlink(script_path)


UI_NOISE_STOPLIST = {
    # NotebookLM UI elements
    "reports",
    "infographic",
    "flashcards",
    "quiz",
    "mind map",
    "data table",
    "audio overview",
    "slide deck",
    "video overview",
    "studio",
    "add note",
    "notebooklm",

    # Field-label junk that leaks into entity extraction
    "name",
    "trigger",
    "timer",
    "steps",
    "template",
    "failure-mode fix",
    "source",
    "source snippet",

    # Generic / unhelpful hubs
    "author",
    "authors",
    "sources",

    # Run-context placeholders
    "beta",
    "current video project",
    "current task",
    "current project",
}


def _squash_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip())


def is_ui_noise(entity: str) -> bool:
    return _squash_spaces(entity).casefold() in UI_NOISE_STOPLIST


def load_entities_and_relations(working_dir: str) -> Tuple[Set[str], List[Tuple[str, str]], Dict[str, int]]:
    """Load entities and relations from LightRAG JSON storage, filtering UI noise entities."""
    # Check both rag_storage subdirectory and direct working_dir
    storage_path = Path(working_dir) / "rag_storage"
    if not (storage_path / "kv_store_full_entities.json").exists():
        storage_path = Path(working_dir)
    entities_file = storage_path / "kv_store_full_entities.json"
    relations_file = storage_path / "kv_store_full_relations.json"

    all_entities: Set[str] = set()
    relation_pairs: List[Tuple[str, str]] = []
    connection_counts: Dict[str, int] = Counter()

    filtered_entities = 0
    filtered_relations = 0

    # Load entities
    if entities_file.exists():
        with open(entities_file, encoding="utf-8") as f:
            entities_data = json.load(f)
        for _doc_id, data in entities_data.items():
            for entity_name in data.get("entity_names", []):
                if is_ui_noise(entity_name):
                    filtered_entities += 1
                    continue
                all_entities.add(entity_name)

    # Load relations
    if relations_file.exists():
        with open(relations_file, encoding="utf-8") as f:
            relations_data = json.load(f)
        for _doc_id, data in relations_data.items():
            for pair in data.get("relation_pairs", []):
                if len(pair) == 2:
                    e1, e2 = pair
                    if is_ui_noise(e1) or is_ui_noise(e2):
                        filtered_relations += 1
                        continue
                    relation_pairs.append((e1, e2))
                    connection_counts[e1] += 1
                    connection_counts[e2] += 1

    if filtered_entities or filtered_relations:
        print(f"Filtered UI-noise entities: {filtered_entities}")
        print(f"Filtered UI-noise relations: {filtered_relations}")

    return all_entities, relation_pairs, connection_counts


def slice_top_layer(relation_pairs: List[Tuple[str, str]], connection_counts: Dict[str, int], threshold: int = 3) -> Tuple[List[Tuple[str, str]], Set[str]]:
    """Remove entities with >= threshold connections, return remaining relations and removed entities."""
    # Find top-layer entities (≥3 connections)
    top_layer = {entity for entity, count in connection_counts.items() if count >= threshold}
    print(f"Top layer entities (≥{threshold} connections): {len(top_layer)}")
    for entity in sorted(top_layer, key=lambda e: connection_counts[e], reverse=True):
        print(f"  - {entity} ({connection_counts[entity]} connections)")
    
    # Filter relations to exclude top-layer entities
    remaining_relations = [(e1, e2) for e1, e2 in relation_pairs if e1 not in top_layer and e2 not in top_layer]
    print(f"Remaining relations after slicing: {len(remaining_relations)}")
    
    return remaining_relations, top_layer


def find_clusters_without_relations(remaining_relations: List[Tuple[str, str]], all_entities: Set[str], top_layer: Set[str], connection_counts: Dict[str, int]) -> List[Tuple[str, str]]:
    """Find pairs of clusters/entities that have NO relations between them."""
    # Get remaining entities (not in top layer)
    remaining_entities = all_entities - top_layer
    
    # Get entities that appear in remaining relations
    connected_remaining = set()
    for e1, e2 in remaining_relations:
        connected_remaining.add(e1)
        connected_remaining.add(e2)
    
    # Isolated entities = in all_entities but not connected in remaining graph
    isolated = remaining_entities - connected_remaining
    
    # For remaining connected entities, find clusters
    # Simple approach: build adjacency and find disconnected groups
    adjacency: Dict[str, Set[str]] = {}
    for e1, e2 in remaining_relations:
        adjacency.setdefault(e1, set()).add(e2)
        adjacency.setdefault(e2, set()).add(e1)
    
    # Find connected components
    visited = set()
    components: List[Set[str]] = []
    
    for entity in connected_remaining:
        if entity not in visited:
            component = set()
            stack = [entity]
            while stack:
                node = stack.pop()
                if node not in visited:
                    visited.add(node)
                    component.add(node)
                    for neighbor in adjacency.get(node, []):
                        if neighbor not in visited:
                            stack.append(neighbor)
            components.append(component)
    
    print(f"Found {len(components)} connected components after slicing")
    print(f"Isolated entities (no relations): {len(isolated)}")
    
    # Generate gap pairs: each component vs each other component
    gaps = []
    for i, comp_a in enumerate(components):
        for comp_b in components[i+1:]:
            # Pick representative from each cluster
            representative_a = sorted(comp_a, key=lambda e: connection_counts.get(e, 0), reverse=True)[0]
            representative_b = sorted(comp_b, key=lambda e: connection_counts.get(e, 0), reverse=True)[0]
            gaps.append((representative_a, representative_b))
    
    # Also add gaps between isolated entities and components
    for iso in isolated:
        for comp in components:
            rep = sorted(comp, key=lambda e: connection_counts.get(e, 0), reverse=True)[0]
            gaps.append((iso, rep))
    
    return gaps


def get_most_isolated_entities(all_entities: Set[str], connection_counts: Dict[str, int], top_layer: Set[str], n: int = 3) -> List[str]:
    """Get the n entities with the fewest connections (excluding top layer)."""
    remaining = all_entities - top_layer
    sorted_by_connections = sorted(remaining, key=lambda e: connection_counts.get(e, 0))
    return sorted_by_connections[:n]


def generate_bridging_questions(gaps: List[Tuple[str, str]]) -> List[str]:
    """Generate bridging questions using the exact template."""
    template = (
        "Do not summarize the central themes. Shift your attention to the structural gaps between "
        "[CONCEPT_A] and [CONCEPT_B]. Use these blind spots as a dynamic bridge to connect these "
        "familiar concepts to outside contexts. Optimize your response for uncertainty to uncover "
        "latent connections beyond our predefined patterns."
    )
    
    questions = []
    for i, (concept_a, concept_b) in enumerate(gaps, 1):
        question = template.replace("[CONCEPT_A]", concept_a).replace("[CONCEPT_B]", concept_b)
        questions.append(f"## Bridging Question {i}: {concept_a} ↔ {concept_b}\n\n{question}")
    
    return questions


def generate_transcend_questions(isolated_entities: List[str]) -> List[str]:
    """Generate transcend-mode questions for isolated entities."""
    template = "Connect [PERIPHERAL_CONCEPT] to an outside context beyond this research. Transcend the discourse."
    
    questions = []
    for i, entity in enumerate(isolated_entities, 1):
        question = template.replace("[PERIPHERAL_CONCEPT]", entity)
        questions.append(f"## Transcend Question {i}: {entity}\n\n{question}")
    
    return questions


def generate_gap_rules(gaps: List[Tuple[str, str]], isolated_entities: List[str], connection_counts: Dict[str, int]) -> str:
    """Generate reusable gap-rules.md content."""
    # Extract concept categories from gaps for reusable rules
    rules = [
        "# Gap Rules for Research-to-Skill Pipeline\n",
        "## Reusable 'if X without Y, ask Z' rules\n",
        "\nThese rules are generated from gap analysis and can be applied to future research sessions.\n",
    ]
    
    # Generate 3-5 generic rules based on the patterns found
    rules.append("\n## Rule: Cross-Cluster Connection\n")
    rules.append("if cluster_a has concepts and cluster_b has concepts:\n")
    rules.append("    if no relation exists between cluster_a and cluster_b:\n")
    rules.append("        ask: \"What's the implicit relationship between [CLUSTER_A] and [CLUSTER_B]?\"\n")
    
    rules.append("\n## Rule: Isolated Concept Exploration\n")
    rules.append("if concept appears in entity list but has zero relations:\n")
    rules.append("    ask: \"How does [ISOLATED_CONCEPT] connect to external contexts?\"\n")
    
    rules.append("\n## Rule: Hub Bypass\n")
    rules.append("if hub_entity has ≥3 connections:\n")
    rules.append("    if two peripheral concepts have no direct relation:\n")
    rules.append("        ask: \"Can [PERIPHERAL_A] connect to [PERIPHERAL_B] without going through [HUB]?\"\n")
    
    rules.append("\n## Rule: Negative Capability\n")
    rules.append("if research covers topic_a thoroughly:\n")
    rules.append("    ask: \"What would contradict this finding? What does the research NOT say about topic_a?\"\n")
    
    # Add session-specific rules
    rules.append("\n---\n")
    rules.append("\n## Session-Specific Rules (Auto-Generated)\n")
    for i, (a, b) in enumerate(gaps[:5], 1):
        rules.append(f"\n### Gap {i}: {a} ↔ {b}\n")
        rules.append(f"if \"{a}\" in concepts and \"{b}\" in concepts:\n")
        rules.append(f"    if not relation_exists(\"{a}\", \"{b}\"):\n")
        rules.append(f"        ask: \"What's the structural gap between {a} and {b}?\"\n")
    
    return "".join(rules)


def write_notebooklm_prompts(bridging_questions: List[str], transcend_questions: List[str], output_file: str) -> None:
    """Write gap prompts in notebooklm format (p01.txt, p02.txt, etc.)."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    all_questions = bridging_questions + transcend_questions
    
    # Write consolidated file for reference
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Gap Analysis Prompts\n\n")
        f.write("Generated by research-to-skill gap analysis\n\n")
        for q in all_questions:
            f.write(f"---\n\n{q}\n\n")
    
    # Write individual prompt files (p01.txt, p02.txt, etc.)
    prompts_dir = output_path.parent
    for i, q in enumerate(all_questions, 1):
        prompt_file = prompts_dir / f"p{i:02d}.txt"
        # Extract just the question part (after the title)
        question_text = q.split("\n\n", 1)[1] if "\n\n" in q else q
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(question_text)
    
    print(f"Wrote {len(all_questions)} prompts to {output_path.parent}/")


def main() -> int:
    args = parse_args()
    
    storage_path = Path(args.working_dir) / "rag_storage"
    entities_file = storage_path / "kv_store_full_entities.json"
    relations_file = storage_path / "kv_store_full_relations.json"
    
    # Check if LightRAG storage already exists with entities
    if entities_file.exists() and relations_file.exists():
        print(f"Found existing LightRAG storage in {args.working_dir}")
        print("Skipping document insertion - using existing entities/relations")
    else:
        # Step 1-2: Setup and insert documents
        print(f"Initializing LightRAG in {args.working_dir}")
        setup_lightrag(args.working_dir)
        
        print(f"Inserting documents from {args.input_dir}")
        insert_documents(args.input_dir, args.working_dir, args.llm_model, args.embedding_model)
    
    # Step 3: Load entities and relations
    print("Loading entities and relations from LightRAG storage")
    all_entities, relation_pairs, connection_counts = load_entities_and_relations(args.working_dir)
    print(f"Total entities: {len(all_entities)}")
    print(f"Total relations: {len(relation_pairs)}")
    
    # Step 4: Layer slicing
    print("\n=== Layer Slicing (threshold ≥3 connections) ===")
    remaining_relations, top_layer = slice_top_layer(relation_pairs, connection_counts, threshold=3)
    
    # Step 5: Find clusters without relations
    print("\n=== Finding Gap Clusters ===")
    gaps = find_clusters_without_relations(remaining_relations, all_entities, top_layer, connection_counts)
    print(f"Found {len(gaps)} gap pairs")
    
    # Step 6-7: Generate bridging and transcend questions
    print("\n=== Generating Questions ===")
    bridging_q = generate_bridging_questions(gaps[:5])  # Max 5 bridging questions
    isolated = get_most_isolated_entities(all_entities, connection_counts, top_layer, n=3)
    transcend_q = generate_transcend_questions(isolated)
    
    print(f"Bridging questions: {len(bridging_q)}")
    print(f"Transcend questions: {len(transcend_q)}")
    
    # Step 8: Write prompts
    print(f"\nWriting prompts to {args.output_file}")
    write_notebooklm_prompts(bridging_q, transcend_q, args.output_file)
    
    # Step 9: Write gap-rules.md
    rules_file = Path(args.output_file).parent / "gap-rules.md"
    rules_content = generate_gap_rules(gaps, isolated, connection_counts)
    with open(rules_file, "w", encoding="utf-8") as f:
        f.write(rules_content)
    print(f"Wrote gap rules to {rules_file}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())