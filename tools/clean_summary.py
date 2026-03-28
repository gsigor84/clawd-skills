#!/usr/bin/env python3
"""clean_summary.py

Deduplicate and normalise NotebookLM summaries into a clean, consistent technique list.

Supported technique formats:
1) Heading blocks (used by enriched-summary.md):
   ## Technique Name
   **Trigger:** ...
   **Timer:** ...
   **Steps:** ...
   **Template:** ...
   **Failure-mode fix:** ...
   **Source:** ...

2) Pipe-separated positional:
   Name | Trigger | Timer | Steps | Template | Failure-mode fix | Source

3) Pipe-separated labelled:
   Name: X | Trigger: Y | Timer: Z | ...
   **Name** | X   (and other fields in same row)

4) Dash-label blocks:
   - Name: X
   - Trigger: Y
   - Timer: Z
   ...

5) Bold-label newline blocks:
   **Name** | X
   **Trigger** | Y
   **Timer** | Z
   ...

Deduping:
- Case-insensitive
- Strips leading articles (the/a/an)

Removes broken entries where the technique name is a field label (Name/Trigger/Timer/...).

Output format:

## Technique Name
**Trigger:** ...
**Timer:** ...
**Steps:** ...
**Template:** ...
**Failure-mode fix:** ...
**Source:** ...
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


OUT_FIELDS = [
    "Trigger",
    "Timer",
    "Steps",
    "Template",
    "Failure-mode fix",
    "Source",
]

ARTICLE_RE = re.compile(r"^(?:the|a|an)\s+", re.IGNORECASE)

NAME_STOPLIST = {
    "name",
    "trigger",
    "timer",
    "steps",
    "template",
    "failure-mode fix",
    "failure mode fix",
    "source",
    "source snippet",
}

FIELD_ALIASES = {
    "failure mode fix": "Failure-mode fix",
    "failure-mode fix": "Failure-mode fix",
    "failure_mode_fix": "Failure-mode fix",
    "source snippet": "Source",
    "source": "Source",
}


@dataclass
class Technique:
    name: str
    fields: Dict[str, str]
    raw_order: int


def squash_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip())


def normalise_name(name: str) -> str:
    name = str(name).strip()
    name = re.sub(r"^[\-\*\u2022\s]+", "", name)
    name = re.sub(r"^Name\s*:\s+", "", name, flags=re.IGNORECASE)
    return squash_spaces(name)


def is_bad_name(name: str) -> bool:
    return normalise_name(name).casefold() in NAME_STOPLIST


def dedupe_key(name: str) -> str:
    n = normalise_name(name)
    n = ARTICLE_RE.sub("", n).strip()
    return squash_spaces(n).casefold()


def normalise_field_key(key: str) -> str:
    k = squash_spaces(key).rstrip(":").strip()
    k_low = k.lower()
    if k_low in FIELD_ALIASES:
        return FIELD_ALIASES[k_low]
    # canonicalise
    for f in ["Name", *OUT_FIELDS, "Source snippet"]:
        if f.lower() == k_low:
            return "Source" if f == "Source snippet" else f
    return k


def strip_md_bold(s: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"\1", s)


def parse_pipe_row(line: str) -> List[str] | None:
    if "|" not in line:
        return None
    if re.match(r"^\s*\|", line):
        return None
    cells = [c.strip() for c in line.split("|")]
    if len(cells) < 2:
        return None
    return cells


def parse_labeled_pipe_cells(cells: List[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for cell in cells:
        if not cell:
            continue
        cell2 = strip_md_bold(cell)
        m = re.match(
            r"^(Name|Trigger|Timer|Steps|Template|Failure[- ]mode fix|Source snippet|Source)\s*[:]?\s*(.*)$",
            cell2,
            re.IGNORECASE,
        )
        if m:
            k = normalise_field_key(m.group(1))
            v = m.group(2).strip()
            if k and v:
                out[k] = v
    return out


def parse_techniques(md: str) -> List[Technique]:
    lines = md.splitlines()
    techs: List[Technique] = []
    order = 0

    current_name: str | None = None
    current_fields: Dict[str, List[str]] = {}

    def flush():
        nonlocal current_name, current_fields, order
        if not current_name:
            return
        name = normalise_name(current_name)
        if is_bad_name(name):
            current_name = None
            current_fields = {}
            return
        joined = {k: "\n".join(v).strip() for k, v in current_fields.items()}
        # accept if it has at least one non-empty field besides name
        other = [v for k, v in joined.items() if k != "Name" and v.strip()]
        if other:
            # map source snippet
            if "Source" not in joined and "Source snippet" in joined:
                joined["Source"] = joined.get("Source snippet", "")
            techs.append(Technique(name=name, fields=joined, raw_order=order))
            order += 1
        current_name = None
        current_fields = {}

    def start(name: str):
        nonlocal current_name, current_fields
        flush()
        current_name = normalise_name(name)
        current_fields = {"Name": [current_name]}

    # Patterns
    dash_name = re.compile(r"^\s*[-*\u2022]\s*Name\s*[:|]\s*(.+?)\s*$", re.IGNORECASE)
    dash_field = re.compile(
        r"^\s*[-*\u2022]\s*(Trigger|Timer|Steps|Template|Failure[- ]mode fix|Source snippet|Source)\s*[:|]\s*(.*)$",
        re.IGNORECASE,
    )

    bold_label_pipe = re.compile(
        r"^\s*\*\*(Name|Trigger|Timer|Steps|Template|Failure[- ]mode fix|Source snippet|Source)\*\*\s*\|\s*(.*)$",
        re.IGNORECASE,
    )

    plain_label_pipe = re.compile(
        r"^\s*(Name|Trigger|Timer|Steps|Template|Failure[- ]mode fix|Source snippet|Source)\s*\|\s*(.*)$",
        re.IGNORECASE,
    )

    heading = re.compile(r"^\s*##\s+(.+?)\s*$")
    bold_label_colon = re.compile(
        r"^\s*\*\*(Trigger|Timer|Steps|Template|Failure[- ]mode fix|Source snippet|Source)\*\*\s*:\s*(.*)$",
        re.IGNORECASE,
    )
    # enriched-summary.md actually has: **Trigger:** (bold includes the colon)
    bold_label_colon2 = re.compile(
        r"^\s*\*\*(Trigger|Timer|Steps|Template|Failure[- ]mode fix|Source snippet|Source)\s*:\*\*\s*(.*)$",
        re.IGNORECASE,
    )

    i = 0
    while i < len(lines):
        line = lines[i]

        # Heading-based technique
        hm = heading.match(line)
        if hm:
            cand = hm.group(1)
            if not is_bad_name(cand):
                start(cand)
            i += 1
            continue

        # Bold label colon (for heading blocks)
        bm = bold_label_colon.match(line) or bold_label_colon2.match(line)
        if bm and current_name is not None:
            k = normalise_field_key(bm.group(1))
            v = bm.group(2).rstrip()
            current_fields.setdefault(k, []).append(v)
            i += 1
            continue

        # Pipe row single-line techniques
        cells = parse_pipe_row(line)
        if cells:
            labelled = parse_labeled_pipe_cells(cells)
            if labelled.get("Name"):
                nm = labelled["Name"]
                if not is_bad_name(nm) and any(v.strip() for k, v in labelled.items() if k != "Name"):
                    fields = dict(labelled)
                    fields["Name"] = normalise_name(nm)
                    techs.append(Technique(name=fields["Name"], fields=fields, raw_order=order))
                    order += 1
                i += 1
                continue

            # positional: Name | Trigger | Timer ...
            if cells and cells[0] and not re.match(r"^(Trigger|Timer|Steps|Template|Failure)\b", strip_md_bold(cells[0]), re.IGNORECASE):
                nm = strip_md_bold(cells[0]).strip()
                if not is_bad_name(nm):
                    fields = {
                        "Name": normalise_name(nm),
                        "Trigger": strip_md_bold(cells[1]).strip() if len(cells) > 1 else "",
                        "Timer": strip_md_bold(cells[2]).strip() if len(cells) > 2 else "",
                        "Steps": strip_md_bold(cells[3]).strip() if len(cells) > 3 else "",
                        "Template": strip_md_bold(cells[4]).strip() if len(cells) > 4 else "",
                        "Failure-mode fix": strip_md_bold(cells[5]).strip() if len(cells) > 5 else "",
                        "Source": strip_md_bold(cells[6]).strip() if len(cells) > 6 else "",
                    }
                    other = [v for k, v in fields.items() if k != "Name" and v.strip()]
                    if other:
                        techs.append(Technique(name=fields["Name"], fields=fields, raw_order=order))
                        order += 1
                i += 1
                continue

        # Dash-label blocks
        m = dash_name.match(line)
        if m:
            start(m.group(1))
            i += 1
            continue
        if current_name is not None:
            fm = dash_field.match(line)
            if fm:
                k = normalise_field_key(fm.group(1))
                v = fm.group(2).rstrip()
                current_fields.setdefault(k, []).append(v)
                i += 1
                continue

        # Bold/Plain label pipe blocks
        bm2 = bold_label_pipe.match(line)
        pm2 = plain_label_pipe.match(line)
        m2 = bm2 or pm2
        if m2:
            k = normalise_field_key(m2.group(1))
            v = m2.group(2).rstrip()
            if k.lower() == "name":
                start(v)
            else:
                if current_name is not None:
                    current_fields.setdefault(k, []).append(v)
            i += 1
            continue

        # Continuation lines
        if current_name is not None and line.strip():
            last_key = list(current_fields.keys())[-1]
            if line.startswith(" ") or line.startswith("\t") or line.lstrip().startswith(("-", "*", "1.", "2.", "3.")):
                current_fields.setdefault(last_key, []).append(line.rstrip())
                i += 1
                continue

        # Blank line ends a block
        if current_name is not None and not line.strip():
            flush()

        i += 1

    flush()
    return techs


def dedupe(techniques: List[Technique]) -> Tuple[List[Technique], int]:
    seen: set[str] = set()
    out: List[Technique] = []
    dups = 0
    for t in techniques:
        key = dedupe_key(t.name)
        if key in seen:
            dups += 1
            continue
        seen.add(key)
        out.append(t)
    return out, dups


def render_clean(techniques: List[Technique]) -> str:
    chunks: List[str] = []
    chunks.append("# Clean Summary (deduplicated)\n")
    for t in techniques:
        chunks.append(f"\n## {t.name}\n")
        for f in OUT_FIELDS:
            val = (t.fields.get(f, "") or "").strip() or "(missing)"
            chunks.append(f"**{f}:** {val}\n")
    return "".join(chunks).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    md = Path(args.input).expanduser().read_text(encoding="utf-8", errors="replace")

    techniques = parse_techniques(md)
    deduped, dups = dedupe(techniques)

    out_path = Path(args.output).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_clean(deduped), encoding="utf-8")

    print(f"found={len(techniques)}")
    print(f"duplicates_removed={dups}")
    print(f"unique={len(deduped)}")
    print(f"written={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
