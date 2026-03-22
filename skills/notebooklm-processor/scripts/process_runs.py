#!/opt/anaconda3/bin/python3
"""NotebookLM processor — offline processing of notebooklm-fetcher artifacts.

- Scans runs dir for *.meta.json
- Groups by prompt_number
- Picks latest ok else latest partial
- Extracts assistant raw text from snapshot.json deterministically
- Extracts goal-relevant insights (SKILL.md agent builder)
- Rewrites progress markdown from scratch

No Tandem calls.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Optional OCR dependencies (installed on-demand)
try:
    import pytesseract  # type: ignore
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover
    pytesseract = None
    Image = None


GOAL = "Build an AI agent that creates OpenClaw SKILL.md files"
LOG_DIR_DEFAULT = "/Users/igorsilva/clawd/tmp/logs"
UI_NOISE = {
    "Chat",
    "Studio",
    "Sources",
    "Submit",
    "Save to note",
    "Configure notebook",
    "Chat options",
    "Copy summary",
    "Good summary",
    "Bad summary",
    "Add sources",
    "Select all sources",
    "NotebookLM can be inaccurate; please double-check its responses.",
    # NotebookLM Studio panel noise
    "Audio Overview",
    "Slide deck",
    "Video Overview",
    "Mind Map",
    "Reports",
    "Flashcards",
    "Quiz",
    "Infographic",
    "Data table",
    "Studio output will be saved here.",
    "After adding sources, click to add Audio Overview, study guide, mind map and more!",
    "Add note",
    "Thinking…",
    "Thinking...",
    "🐿️",
}

# Regex filters for DOM snapshots: strip citations/UI crumbs so we keep only main response text.
UI_NOISE_REGEX = [
    re.compile(r"^\s*$"),  # empty
    re.compile(r"^\s*[\d,]+\s*$"),  # bare citation numbers
    re.compile(r"^\s*[\.,;:•\-—]+\s*$"),  # punctuation-only
    re.compile(r"^\s*\d+\s+sources\s*$", re.I),
]

# Only used by downstream validation scripts; not applied as a filter inside the processor.
SIDEBAR_NOISE_WORDS = re.compile(r"\b(sources|studio|add sources|mind map|flashcards|quiz|infographic|data table|configure notebook|chat options)\b", re.I)

PLACEHOLDER_LINES = {
    "consulting your sources...",
    "checking your files...",
    "checking your uploads...",
    "reading full chapters...",
    "reading through pages...",
    "reading your sources...",
    "scanning your sources...",
    "assessing relevance...",
    "examining the specifics...",
    "finding relevant info...",
    "retrieving details...",
    "getting the context...",
    "checking the scope...",
    "processing material...",
    "sifting through pages...",
    "parsing the data...",
    "looking at sources...",
    "analyzing your files...",
    "opening your notes...",
    "exploring your material...",
    "gathering the facts...",
    "searching your docs...",
    "scanning the text...",
}


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def log_line(log_path: Path, prompt_number: Optional[int], event: str, status: str, detail: str = "") -> None:
    ts = utc_now_iso()
    pn = f"prompt-{int(prompt_number):02d}" if prompt_number is not None else "prompt-??"
    msg = f"{ts} | {pn} | {event} | {status}"
    if detail:
        msg += f" | {detail}"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def parse_iso(s: str) -> Optional[dt.datetime]:
    if not s:
        return None
    try:
        # allow Z
        s = s.replace("Z", "+00:00")
        return dt.datetime.fromisoformat(s)
    except Exception:
        return None


def filename_timestamp(run_id: str) -> Optional[dt.datetime]:
    # RUN_ID starts with YYYYMMDD-HHMM
    m = re.match(r"^(\d{8})-(\d{4})_", run_id)
    if not m:
        return None
    try:
        return dt.datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M")
    except Exception:
        return None


def ws_collapse(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


@dataclass
class Run:
    run_id: str
    meta_path: Path
    meta: Dict[str, Any]

    @property
    def prompt_number(self) -> Optional[int]:
        return self.meta.get("prompt_number")

    @property
    def status(self) -> str:
        return (self.meta.get("result") or {}).get("status") or "unknown"

    @property
    def partial(self) -> bool:
        return bool((self.meta.get("result") or {}).get("partial"))

    @property
    def created_at(self) -> Optional[dt.datetime]:
        return parse_iso(self.meta.get("created_at", ""))

    def artifact_path(self, key: str) -> Optional[Path]:
        # Prefer meta.artifacts paths if present
        ap = (self.meta.get("artifacts") or {}).get(key)
        if ap:
            return Path(ap)
        return None

    def snapshot_path(self) -> Path:
        p = self.artifact_path("snapshot_json")
        if p:
            return p
        return self.meta_path.with_suffix("").with_suffix(".snapshot.json")

    def prompt_path(self) -> Path:
        p = self.artifact_path("prompt_txt")
        if p:
            return p
        return self.meta_path.with_suffix("").with_suffix(".prompt.txt")


def load_runs(runs_dir: Path) -> List[Run]:
    runs: List[Run] = []
    for mp in sorted(runs_dir.glob("*.meta.json")):
        try:
            meta = json.loads(mp.read_text(encoding="utf-8"))
            run_id = meta.get("run_id") or mp.name.replace(".meta.json", "")
            runs.append(Run(run_id=run_id, meta_path=mp, meta=meta))
        except Exception:
            continue
    return runs


def pick_latest(runs: List[Run]) -> Optional[Run]:
    if not runs:
        return None

    def sort_key(r: Run):
        ca = r.created_at
        ft = filename_timestamp(r.run_id)
        # prefer created_at; fallback filename timestamp; fallback lexical
        return (
            ca or ft or dt.datetime.min,
            r.run_id,
        )

    # prefer ok, else partial
    oks = [r for r in runs if r.status == "ok"]
    if oks:
        return sorted(oks, key=sort_key)[-1]
    partials = [r for r in runs if r.status == "partial"]
    if partials:
        return sorted(partials, key=sort_key)[-1]
    return None


def _static_text_values(lines: List[str]) -> List[Tuple[int, str]]:
    vals: List[Tuple[int, str]] = []
    for i, l in enumerate(lines):
        if "StaticText" not in l:
            continue
        m = re.search(r'StaticText "(.*)" \[@e\d+\]', l)
        if m:
            vals.append((i, m.group(1)))
    return vals


def extract_static_text_after_prompt(snapshot_text: str, prompt_text: str, prompt_starters: List[str]) -> Tuple[str, str]:
    """Return (raw_extracted, mode).

    Goal: extract the assistant response *for this prompt*, not the whole chat.

    Modes:
    - prompt_match: extracted after matching prompt text (robust match)
    - after_sources: fallback extracted after last "Sources" StaticText (bounded by next prompt)
    - tail50: fallback last 50 StaticText lines
    - not_found: no extraction possible
    """
    lines = snapshot_text.splitlines()
    st_vals = _static_text_values(lines)

    starters = [ws_collapse(s).lower() for s in prompt_starters if ws_collapse(s)]

    def _is_noise_line(t: str) -> bool:
        tt = ws_collapse(t)
        if not tt:
            return True
        if tt in UI_NOISE:
            return True
        return any(rx.search(tt) for rx in UI_NOISE_REGEX)

    def clean(seq: List[str]) -> str:
        # de-dup consecutive
        dedup: List[str] = []
        for t in seq:
            if not dedup or dedup[-1] != t:
                dedup.append(t)
        cleaned = [ws_collapse(t) for t in dedup if not _is_noise_line(t)]
        return "\n".join(cleaned).strip()

    def is_prompt_start(txt: str) -> bool:
        t = ws_collapse(txt).lower()
        if not t:
            return False
        # heuristics: common prompt openings + known starters
        if t.startswith("you are ") or t.startswith("review all my uploaded sources"):
            return True
        return any(t.startswith(s) for s in starters)

    # Prefer to work on the chat transcript extracted after the last "Sources" marker.
    # This avoids DOM/virtualization issues where the assistant response isn't located immediately after the prompt.
    sources_idx: Optional[int] = None
    for i, v in st_vals:
        if v.strip().lower() == "sources":
            sources_idx = i

    transcript_vals: List[str] = []
    if sources_idx is not None:
        transcript_vals = [v for i, v in st_vals if i > sources_idx]
    else:
        transcript_vals = [v for _, v in st_vals]

    # clean transcript
    def clean_vals(seq: List[str]) -> List[str]:
        dedup: List[str] = []
        for t in seq:
            if not dedup or dedup[-1] != t:
                dedup.append(t)
        out: List[str] = []
        for t in dedup:
            if _is_noise_line(t):
                continue
            out.append(ws_collapse(t))
        return out

    transcript_vals = clean_vals(transcript_vals)

    def segment_after(match_idx: int) -> str:
        out: List[str] = []
        for v in transcript_vals[match_idx + 1 :]:
            if out and is_prompt_start(v):
                break
            out.append(v)
        return clean(out)

    # 1) Find prompt line inside transcript (exact or first-line)
    target = ws_collapse(prompt_text).lower()
    first_line = ws_collapse(prompt_text.splitlines()[0] if prompt_text else "").lower()

    match_idx: Optional[int] = None
    if target:
        for i, v in enumerate(transcript_vals):
            if target in ws_collapse(v).lower():
                match_idx = i
    if match_idx is None and first_line:
        for i, v in enumerate(transcript_vals):
            if first_line in ws_collapse(v).lower():
                match_idx = i

    # 1b) Keyword-based match within transcript
    if match_idx is None and prompt_text:
        stop = {
            "the","and","from","with","that","this","your","you","are","for","into","across","using",
            "all","my","to","of","a","an","in","on","as","is","it","be","or","by","at","we",
            "include","includes","including","each","must","should","focus","avoid","based","provide",
        }
        words = [w.lower() for w in re.findall(r"[A-Za-z]{5,}", prompt_text[:240])]
        kws: List[str] = []
        for w in words:
            if w in stop:
                continue
            if w not in kws:
                kws.append(w)
        kws = kws[:8]

        def score(v: str) -> int:
            vv = ws_collapse(v).lower()
            return sum(1 for k in kws if k in vv)

        best = None
        for i, v in enumerate(transcript_vals):
            sc = score(v)
            if sc >= 2:
                best = i
        if best is not None:
            match_idx = best

    if match_idx is not None:
        raw = segment_after(match_idx)
        if raw:
            return raw, "prompt_match"

    # 2) Fallback: return entire transcript (still bounded by sources)
    raw2 = clean(transcript_vals)
    if raw2:
        return raw2, "after_sources"

    # 3) Tail fallback: last 50 StaticText lines
    tail = [v for v in transcript_vals[-50:]]
    raw3 = clean(tail)
    if raw3:
        return raw3, "tail50"

    return "", "not_found"


def is_placeholder_only(raw_text: str) -> bool:
    """True if extracted text looks like NotebookLM loading placeholders."""
    lines = [ws_collapse(l).lower() for l in (raw_text or "").splitlines() if ws_collapse(l)]
    if not lines:
        return True
    # If every line is a known placeholder, treat as placeholder-only.
    return all(l in PLACEHOLDER_LINES for l in lines)


def ocr_extract_from_images(image_paths: List[Path]) -> str:
    """Run OCR over provided images and return merged, de-noised text.

    Goal: keep only the *main chat response text*.
    Aggressively drop sidebar/UI chrome and citation crumbs.
    """
    if not image_paths:
        return ""
    if pytesseract is None or Image is None:
        return ""

    chunks: List[str] = []
    # Crop to center chat column: x=400..1100 of a 1332px viewport (scale if needed)
    x1_frac = 400.0 / 1332.0
    x2_frac = 1100.0 / 1332.0

    for p in image_paths:
        try:
            img = Image.open(p)
            w, h = img.size
            x1 = int(max(0, min(w, round(w * x1_frac))))
            x2 = int(max(0, min(w, round(w * x2_frac))))
            if x2 > x1 + 10:
                img = img.crop((x1, 0, x2, h))
            txt = pytesseract.image_to_string(img)
            chunks.append(txt)
        except Exception:
            continue

    merged = "\n".join(chunks)

    # OCR-specific UI/Chrome patterns
    ocr_noise_regex = [
        re.compile(r"^\s*[\d,]+\s*$"),  # bare numbers
        re.compile(r"^\s*[\.,;:•\-—]+\s*$"),  # punctuation-only
        re.compile(r"^\s*\d+\s+sources\s*$", re.I),
        re.compile(r"^\s*(sources|studio|chat)\s*$", re.I),
        re.compile(r"^\s*(submit|save to note|copy|copy summary)\s*$", re.I),
        re.compile(r"^\s*(configure notebook|chat options)\s*$", re.I),
        re.compile(r"^\s*(rate response as (good|bad))\s*$", re.I),
        re.compile(r"^\s*(stop generating|looking at sources)\s*$", re.I),
        re.compile(r"\.pdf\s*$", re.I),  # source filenames
        re.compile(r"^\s*notebooklm\b", re.I),
        re.compile(r"^\s*google\b", re.I),
    ]

    out_lines: List[str] = []
    seen = set()

    for ln in merged.splitlines():
        l = ws_collapse(ln)
        if not l:
            continue

        ll = l.lower()

        # hard-drop known UI noise
        if l in UI_NOISE:
            continue
        if ll in PLACEHOLDER_LINES:
            continue
        if ll.startswith("notebooklm can be inaccurate"):
            continue

        # drop timestamp-ish / nav crumbs
        if ll.startswith("today") and ("•" in l or "·" in l):
            continue

        # regex noise
        if any(rx.search(l) for rx in ocr_noise_regex):
            continue

        # very short fragments are usually chrome/citations
        if len(l) < 4:
            continue

        # de-dup
        if l in seen:
            continue
        seen.add(l)
        out_lines.append(l)

    # de-dup consecutive
    dedup: List[str] = []
    for l in out_lines:
        if not dedup or dedup[-1] != l:
            dedup.append(l)

    return "\n".join(dedup).strip()


def extract_goal_insights(raw_text: str) -> List[str]:
    """Heuristic extraction: keep only lines likely relevant to building SKILL.md agent.

    Deterministic, non-LLM.
    """
    if not raw_text.strip():
        return []

    keywords = [
        "skill.md",
        "tools",
        "tool",
        "mcp",
        "model context protocol",
        "context engineering",
        "rag",
        "retrieval",
        "memory",
        "reAct",
        "graph",
        "workflow",
        "orchestration",
        "multi-agent",
        "review",
        "critic",
        "qa",
        "benchmarks",
        "reliability",
        "safety",
        "halluc",
        "acceptance",
        "validation",
        "guardrail",
        "return on intelligence",
        "roi",
        "prompt engineering",
        "few-shot",
        "schema",
        "json",
    ]

    out = []
    for ln in raw_text.splitlines():
        l = ln.strip()
        if not l:
            continue
        ll = l.lower()
        if any(k in ll for k in keywords):
            out.append(l)

    # de-dup
    dedup = []
    for t in out:
        if not dedup or dedup[-1] != t:
            dedup.append(t)

    return dedup[:80]


def md_escape_codeblock(s: str) -> str:
    # avoid closing fence
    return s.replace("```", "``\u200b`")


def write_progress(progress_path: Path, selected: Dict[int, Run], extracted: Dict[int, Dict[str, Any]]) -> None:
    lines: List[str] = []
    lines.append(f"# NotebookLM progress — {GOAL}")
    lines.append("")
    lines.append(f"Updated: {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")

    # Status
    lines.append("## Status")
    done = []
    partial = []
    missing = []
    for n in range(1, 18):
        r = selected.get(n)
        if not r:
            missing.append(n)
        elif r.status == "ok":
            done.append(n)
        else:
            partial.append(n)
    lines.append(f"- OK: {done if done else '[]'}")
    lines.append(f"- Partial: {partial if partial else '[]'}")
    lines.append(f"- Missing: {missing if missing else '[]'}")
    lines.append("")

    # Per prompt
    lines.append("## Prompts")
    lines.append("")

    for n in range(1, 18):
        lines.append(f"### Prompt {n:02d}")
        r = selected.get(n)
        if not r:
            lines.append("- Status: missing")
            lines.append("")
            continue

        e = extracted.get(n, {})
        lines.append(f"- Run: `{r.run_id}`")
        lines.append(f"- Status: `{r.status}` (partial={str(r.partial).lower()})")
        if r.created_at:
            lines.append(f"- Created: `{r.created_at.isoformat()}`")
        lines.append(f"- Extraction mode: `{e.get('mode','')}`")
        if e.get("source_snapshot_run_id"):
            lines.append(f"- Source snapshot: `{e.get('source_snapshot_run_id')}`")
        lines.append("")

        raw = e.get("raw", "")
        if raw:
            lines.append("**Raw extracted**")
            lines.append("```")
            lines.append(md_escape_codeblock(raw))
            lines.append("```")
        else:
            lines.append("**Raw extracted**")
            lines.append("(empty — extraction failed or content not present in snapshot)")

        insights = e.get("insights", [])
        lines.append("")
        lines.append("**Goal-relevant insights (heuristic)**")
        if insights:
            for it in insights:
                lines.append(f"- {it}")
        else:
            lines.append("- (none detected)")
        lines.append("")

    # Cross-prompt synthesis
    lines.append("## Cross-prompt synthesis (SKILL.md-agent build)")
    lines.append("")
    lines.append("### Stable build checklist")
    lines.append("- Inputs: required fields for SKILL.md (frontmatter + body) + tool constraints")
    lines.append("- Deterministic validation: schema/fields checks before accepting output")
    lines.append("- Context engineering: retrieve only the relevant doc sections/examples for the current skill")
    lines.append("- Tool/interface standardization: prefer MCP-like adapters / wrappers for integrations")
    lines.append("- Reliability: use critique/review loop; consider graph-constrained workflow in production")
    lines.append("")

    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", default="/Users/igorsilva/clawd/tmp/notebooklm-runs")
    ap.add_argument("--progress-file", default="/Users/igorsilva/clawd/tmp/notebooklm-progress.md")
    ap.add_argument("--log-dir", default=LOG_DIR_DEFAULT)
    ap.add_argument("--only-prompt", type=int, default=None, help="If set, process only this prompt number (still rewrites full progress file, but updates/uses selection/extraction for only that prompt).")
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir)
    progress_path = Path(args.progress_file)
    log_path = Path(args.log_dir) / ("processor-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d") + ".log")

    log_line(log_path, None, "start", "ok", f"runs_dir={runs_dir} | progress_file={progress_path}")

    if not runs_dir.exists() or not runs_dir.is_dir():
        log_line(log_path, None, "scan_runs", "fail", f"runs_dir_not_found={runs_dir}")
        print(f"ERROR: runs dir not found: {runs_dir}", file=sys.stderr)
        return 2

    runs = load_runs(runs_dir)
    if not runs:
        log_line(log_path, None, "scan_runs", "fail", "no_meta_json_parsed")
        print("ERROR: no meta.json runs parsed successfully", file=sys.stderr)
        return 3

    log_line(log_path, None, "scan_runs", "ok", f"runs={len(runs)}")

    grouped: Dict[int, List[Run]] = {}
    for r in runs:
        pn = r.prompt_number
        if pn is None:
            continue
        grouped.setdefault(int(pn), []).append(r)

    selected: Dict[int, Run] = {}
    for pn, rs in grouped.items():
        if args.only_prompt is not None and pn != int(args.only_prompt):
            continue
        pick = pick_latest(rs)
        if pick:
            selected[pn] = pick
            log_line(log_path, pn, "select_run", "ok", f"run_id={pick.run_id} | status={pick.status}")

    # Use the latest available snapshot overall as the canonical chat transcript.
    # Rationale: per-prompt snapshots may be captured while NotebookLM is still "Consulting your sources...";
    # later snapshots typically contain the completed responses in the accumulated chat history.
    all_runs = runs

    def global_sort_key(r: Run):
        return (r.created_at or filename_timestamp(r.run_id) or dt.datetime.min, r.run_id)

    global_candidates = [r for r in all_runs if r.status in ("ok", "partial")]
    global_run: Optional[Run] = sorted(global_candidates, key=global_sort_key)[-1] if global_candidates else None

    global_snap_txt = ""
    if global_run is not None:
        try:
            global_snap_obj = json.loads(global_run.snapshot_path().read_text(encoding="utf-8"))
            global_snap_txt = global_snap_obj.get("snapshot", "")
            log_line(log_path, None, "load_global_snapshot", "ok", f"run_id={global_run.run_id} | chars={len(global_snap_txt)}")
        except Exception as e:
            global_snap_txt = ""
            log_line(log_path, None, "load_global_snapshot", "fail", f"run_id={getattr(global_run,'run_id','')} | error={e}")
    else:
        log_line(log_path, None, "load_global_snapshot", "fail", "no_global_run")

    extracted: Dict[int, Dict[str, Any]] = {}

    # prompt starters for bounding (first lines across selected prompts)
    starters: List[str] = []
    for _pn, _r in grouped.items():
        # starters should reflect the full prompt library, not just selected subset
        try:
            pick = pick_latest(_r)
            if not pick:
                continue
            pt = pick.prompt_path().read_text(encoding="utf-8")
            first = pt.splitlines()[0] if pt.strip() else ""
            if first.strip():
                starters.append(first)
        except Exception:
            continue

    for pn, r in selected.items():
        try:
            prompt_text = r.prompt_path().read_text(encoding="utf-8")
        except Exception:
            prompt_text = ""

        # 0) Preferred path: clipboard-captured response.txt (from fetcher)
        raw = ""
        mode = ""
        src_run_id = r.run_id
        try:
            mp = json.loads(r.meta_path.read_text(encoding="utf-8"))
            resp_path = ((mp.get("artifacts") or {}).get("response_txt"))
            if resp_path and Path(resp_path).exists():
                raw = Path(resp_path).read_text(encoding="utf-8", errors="replace").strip()
                if raw:
                    mode = "clipboard"
        except Exception:
            pass

        # 1) Fallback: snapshot extraction (legacy)
        if not raw:
            snap_txt = ""
            try:
                snap_obj = json.loads(r.snapshot_path().read_text(encoding="utf-8"))
                snap_txt = snap_obj.get("snapshot", "") or ""
            except Exception:
                snap_txt = ""

            # Fallback to global snapshot only if missing/empty
            if not snap_txt and global_snap_txt:
                snap_txt = global_snap_txt
                src_run_id = global_run.run_id if global_run else r.run_id

            raw, mode = extract_static_text_after_prompt(snap_txt, prompt_text, starters)

            # Treat known one-line generation placeholders as effectively empty.
            if raw and ws_collapse(raw).lower() in PLACEHOLDER_LINES:
                raw = ""

            # If prompt snapshot produced nothing, and global exists, try global snapshot.
            if not raw and global_snap_txt and src_run_id == r.run_id:
                raw_g, mode_g = extract_static_text_after_prompt(global_snap_txt, prompt_text, starters)
                if raw_g:
                    raw = raw_g
                    mode = mode_g + "+global"
                    src_run_id = global_run.run_id if global_run else src_run_id

        # 2) No OCR fallback anymore in the primary path.
        # (We keep ocr_extract_from_images for compatibility, but do not run it here.)

        insights = extract_goal_insights(raw)
        extracted[pn] = {
            "raw": raw,
            "mode": mode,
            "insights": insights,
            "source_snapshot_run_id": src_run_id,
        }
        lines_extracted = len(raw.splitlines()) if raw else 0
        st = "ok" if lines_extracted > 0 else "fail"
        log_line(log_path, pn, "extraction", st, f"mode={mode} | lines={lines_extracted} | src={src_run_id}")

    try:
        write_progress(progress_path, selected, extracted)
        log_line(log_path, None, "write_progress", "ok", f"path={progress_path}")
    except Exception as e:
        log_line(log_path, None, "write_progress", "fail", f"error={e}")
        print(f"ERROR: cannot write progress file: {e}", file=sys.stderr)
        return 4

    log_line(log_path, None, "done", "ok", "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
