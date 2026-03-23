#!/opt/anaconda3/bin/python3
"""Parse a /learn-produced *-study-guide.md and emit per-concept JSON files.

Design goals:
- Deterministic parsing of the /learn template.
- Best-effort by default: skip malformed concepts and report why.
- Optional --strict to hard-fail on first structural problem.

Output layout (default):
  ~/clawd/learn/json/<source-title>/
    index.json
    001-concept-slug.json
    002-concept-slug.json

Each concept JSON is small and retrieval-friendly for keyword search + later embedding.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import List, Optional, Tuple


STEP4_RE = re.compile(r"^##\s*STEP\s*4\s*—\s*WRITE\s+STUDY\s+GUIDE\s*$", re.M)
NEXT_STEP_RE = re.compile(r"^##\s*STEP\s*(?P<num>\d+)\s*—\s*", re.M)
HEADER_RE = re.compile(r"^###\s+(?P<num>\d+)\.\s+(?P<title>.+?)\s*$", re.M)


@dataclasses.dataclass
class ConceptBlock:
    index: int
    title: str
    raw: str
    concept_note: Optional[str] = None
    evidence: Optional[str] = None
    backbone_link: Optional[str] = None


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "concept"


def isolate_step4(md: str) -> Optional[str]:
    """Return the markdown inside STEP 4 only, or None if STEP 4 heading not found."""
    m = STEP4_RE.search(md)
    if not m:
        return None
    after = md[m.end():]
    nxt = NEXT_STEP_RE.search(after)
    section = after[:nxt.start()] if nxt else after
    return section.strip() + "\n"


def split_concepts(step4_md: str) -> List[ConceptBlock]:
    matches = list(HEADER_RE.finditer(step4_md))
    blocks: List[ConceptBlock] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(step4_md)
        raw = step4_md[start:end].strip() + "\n"
        idx = int(m.group("num"))
        title = m.group("title").strip()
        blocks.append(ConceptBlock(index=idx, title=title, raw=raw))
    return blocks


def parse_concept_fields(block: ConceptBlock) -> Tuple[bool, List[str]]:
    """Parse Concept Note / Evidence (verbatim) / Backbone Link from a STEP 4 concept block."""
    problems: List[str] = []
    raw = block.raw

    note = re.search(r"\*\*Concept Note\*\*\s*(?P<txt>.*?)(?=\n\s*\*\*Evidence \(verbatim\)\*\*|\Z)", raw, flags=re.S)
    if note:
        block.concept_note = note.group("txt").strip() or None
    else:
        problems.append("missing Concept Note")

    ev = re.search(r"\*\*Evidence \(verbatim\)\*\*\s*(?P<txt>.*?)(?=\n\s*\*\*Backbone Link\*\*|\Z)", raw, flags=re.S)
    if ev:
        block.evidence = ev.group("txt").strip() or None
    else:
        problems.append("missing Evidence (verbatim)")

    bb = re.search(r"\*\*Backbone Link\*\*\s*(?P<txt>.*)\Z", raw, flags=re.S)
    if bb:
        block.backbone_link = bb.group("txt").strip() or None
    else:
        problems.append("missing Backbone Link")

    ok = (block.concept_note is not None) and (block.evidence is not None) and (block.backbone_link is not None)
    return ok, problems


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest /learn *-study-guide.md into per-concept JSON files")
    ap.add_argument("input_md", help="Path to *-study-guide.md")
    ap.add_argument("--out-base", default="/Users/igorsilva/clawd/learn/json", help="Base output directory")
    ap.add_argument("--strict", action="store_true", help="Hard-fail on first structural problem")
    args = ap.parse_args()

    in_path = Path(args.input_md).expanduser().resolve()
    if not in_path.exists() or not in_path.is_file():
        print(f"ERROR: input file not found: {in_path}", file=sys.stderr)
        return 2

    md = in_path.read_text(encoding="utf-8", errors="replace")
    if not md.strip():
        print("ERROR: input file is empty", file=sys.stderr)
        return 2

    source_title = in_path.stem
    # strip -study-guide suffix if present
    if source_title.endswith("-study-guide"):
        source_title = source_title[: -len("-study-guide")]
    source_slug = slugify(source_title)

    out_dir = Path(args.out_base).expanduser().resolve() / source_slug
    out_dir.mkdir(parents=True, exist_ok=True)

    step4 = isolate_step4(md)
    if step4 is None:
        print("ERROR: STEP 4 section not found (expected '## STEP 4 — WRITE STUDY GUIDE')", file=sys.stderr)
        return 2

    concepts = split_concepts(step4)
    if not concepts:
        print("ERROR: no concept headers found inside STEP 4 (expected '### N. Concept Name')", file=sys.stderr)
        return 2

    ingested = []
    skipped = []
    now = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()

    for c in concepts:
        ok, problems = parse_concept_fields(c)

        if not ok:
            if args.strict:
                print(f"ERROR: concept '{c.title}' skipped: {', '.join(problems)}", file=sys.stderr)
                return 3
            skipped.append({"index": c.index, "concept": c.title, "problems": problems})
            continue

        file_name = f"{c.index:03d}-{slugify(c.title)}.json"
        payload = {
            "schema": "clawd.learn.concept.v2",
            "concept": c.title,
            "index": c.index,
            "concept_note": c.concept_note,
            "evidence": c.evidence,
            "backbone_link": c.backbone_link,
            "source": {
                "type": "learn-study-guide-md",
                "md_path": str(in_path),
                "source_title": source_title,
                "generated_at_utc": now,
                "parsed_from": "STEP 4 — WRITE STUDY GUIDE",
            },
            "retrieval": {
                "keywords": [],
                "tags": ["learn", "study-guide", "concept"],
            },
        }

        (out_dir / file_name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        ingested.append({"index": c.index, "concept": c.title, "file": file_name})

    index_payload = {
        "schema": "clawd.learn.study-guide-index.v2",
        "source": {
            "type": "learn-study-guide-md",
            "md_path": str(in_path),
            "source_title": source_title,
            "source_slug": source_slug,
            "generated_at_utc": now,
            "parsed_from": "STEP 4 — WRITE STUDY GUIDE",
        },
        "concepts_total": len(concepts),
        "ingested_count": len(ingested),
        "skipped_count": len(skipped),
        "ingested": ingested,
        "skipped": skipped,
    }
    (out_dir / "index.json").write_text(json.dumps(index_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # DEBUG OUTPUT (MANDATORY)
    print(f"out_dir: {out_dir}")
    print(f"total concepts found: {len(concepts)}")
    print(f"successfully ingested: {len(ingested)}")
    print(f"skipped: {len(skipped)}")
    if skipped:
        print("skip reasons:")
        for s in skipped:
            print(f"- {s['index']:03d} {s['concept']}: {', '.join(s['problems'])}")

    # Also emit a compact JSON summary (useful for tooling)
    summary = {
        "out_dir": str(out_dir),
        "concepts_total": len(concepts),
        "ingested_count": len(ingested),
        "skipped_count": len(skipped),
        "index": str(out_dir / "index.json"),
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
