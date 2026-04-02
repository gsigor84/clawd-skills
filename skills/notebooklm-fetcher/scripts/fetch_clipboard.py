#!/opt/anaconda3/bin/python3
"""NotebookLM fetcher (Tandem) — send one prompt and capture the latest response via clipboard.

Artifacts per run:
- {RUN_ID}.prompt.txt
- {RUN_ID}.response.txt        (raw response captured via pbpaste after clicking "Copy model response to clipboard")
- {RUN_ID}.snapshot.json       (debug)
- {RUN_ID}.screenshot.png      (debug)
- {RUN_ID}.meta.json

Primary completion signal:
- Wait until the latest "Copy model response to clipboard" button is present.

This script intentionally does NO summarization.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover
    Image = None


LOG_DIR_DEFAULT = "/Users/igorsilva/clawd/tmp/logs"
BASE_DEFAULT = "http://127.0.0.1:8765"
TOKEN_PATH_DEFAULT = os.path.expanduser("~/.tandem/api-token")
LEARNINGS_ERRORS_PATH = Path("/Users/igorsilva/clawd/.learnings/ERRORS.md")


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def utc_today() -> str:
    d = dt.datetime.now(dt.timezone.utc).date()
    return d.isoformat()


def next_err_id(existing_text: str) -> str:
    ymd = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    ids = re.findall(rf"\bERR-{ymd}-(\d{{3}})\b", existing_text)
    n = (max([int(x) for x in ids]) + 1) if ids else 1
    return f"ERR-{ymd}-{n:03d}"


def update_or_append_err(
    *,
    pattern_key: str,
    summary: str,
    error_lines: list[str],
    context_lines: list[str],
    suggested_fix_lines: list[str],
    priority: str = "high",
    area: str = "infra",
) -> None:
    """Write a structured ERR entry to ~/clawd/.learnings/ERRORS.md.

    If an entry with the same Pattern-Key exists, increment Recurrence-Count
    and update Last-Seen instead of creating a duplicate.
    """
    LEARNINGS_ERRORS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = ""
    if LEARNINGS_ERRORS_PATH.exists():
        existing = LEARNINGS_ERRORS_PATH.read_text(encoding="utf-8", errors="ignore")
    else:
        existing = "# Errors Log\n\n---\n\n"

    today = utc_today()

    # Try to find existing block containing Pattern-Key.
    key_pat = re.compile(rf"^\s*-\s*Pattern-Key:\s*{re.escape(pattern_key)}\s*$", re.M)
    m = key_pat.search(existing)
    if m:
        # Update the nearest preceding '## [' header block by scanning outward.
        start = existing.rfind("## [", 0, m.start())
        end = existing.find("\n---\n", m.end())
        if start == -1:
            start = 0
        if end == -1:
            end = len(existing)
        block = existing[start:end]

        # Update recurrence count
        rc_re = re.compile(r"^\s*-\s*Recurrence-Count:\s*(\d+)\s*$", re.M)
        rc_m = rc_re.search(block)
        if rc_m:
            rc = int(rc_m.group(1)) + 1
            block2 = rc_re.sub(f"- Recurrence-Count: {rc}", block, count=1)
        else:
            # Insert after Pattern-Key line if missing
            block2 = re.sub(
                rf"(^\s*-\s*Pattern-Key:\s*{re.escape(pattern_key)}\s*$)",
                rf"\1\n- Recurrence-Count: 2",
                block,
                flags=re.M,
                count=1,
            )

        # Update Last-Seen
        ls_re = re.compile(r"^\s*-\s*Last-Seen:\s*(\d{4}-\d{2}-\d{2})\s*$", re.M)
        if ls_re.search(block2):
            block3 = ls_re.sub(f"- Last-Seen: {today}", block2, count=1)
        else:
            block3 = block2 + f"\n- Last-Seen: {today}\n"

        LEARNINGS_ERRORS_PATH.write_text(existing[:start] + block3 + existing[end:], encoding="utf-8")
        return

    # Append new entry
    err_id = next_err_id(existing)
    entry = [
        f"## [{err_id}] notebooklm-fetcher",
        "",
        f"**Logged**: {utc_now_iso()}",
        f"**Priority**: {priority}",
        "**Status**: pending",
        f"**Area**: {area}",
        "",
        "### Summary",
        summary.strip(),
        "",
        "### Error",
        *[f"- {ln}" for ln in error_lines if ln.strip()],
        "",
        "### Context",
        *[f"- {ln}" for ln in context_lines if ln.strip()],
        "",
        "### Suggested Fix",
        *[f"- {ln}" for ln in suggested_fix_lines if ln.strip()],
        "",
        "### Metadata",
        "- Source: error",
        "- Tags: notebooklm, browser-automation, selector-drift, silent-failure",
        f"- Pattern-Key: {pattern_key}",
        "- Recurrence-Count: 1",
        f"- First-Seen: {today}",
        f"- Last-Seen: {today}",
        "",
        "---",
        "",
    ]
    LEARNINGS_ERRORS_PATH.write_text(existing + "\n".join(entry), encoding="utf-8")


def log_line(log_path: Path, prompt_number: int, event: str, status: str, detail: str = "") -> None:
    ts = utc_now_iso()
    pn = f"prompt-{prompt_number:02d}"
    msg = f"{ts} | {pn} | {event} | {status}"
    if detail:
        msg += f" | {detail}"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def local_run_id(prompt_number: int, slug: str, now: Optional[dt.datetime] = None) -> str:
    now = now or dt.datetime.now()
    return now.strftime("%Y%m%d-%H%M") + f"_prompt-{prompt_number:02d}_{slug}"


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "run"


@dataclass
class Tandem:
    base: str
    token: str

    def _curl(self, method: str, path: str, json_body: Optional[dict] = None, out_file: Optional[Path] = None) -> subprocess.CompletedProcess:
        url = self.base.rstrip("/") + path
        cmd = ["curl", "-sS", "-H", f"Authorization: Bearer {self.token}"]
        if method.upper() != "GET":
            cmd += ["-H", "Content-Type: application/json", "-X", method.upper()]
        if json_body is not None:
            cmd += ["-d", json.dumps(json_body)]
        cmd.append(url)

        if out_file is not None:
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "wb") as f:
                return subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def status(self) -> Dict[str, Any]:
        p = self._curl("GET", "/status")
        p.check_returncode()
        return json.loads(p.stdout.decode("utf-8"))

    def navigate(self, url: str) -> Dict[str, Any]:
        p = self._curl("POST", "/navigate", {"url": url})
        p.check_returncode()
        return json.loads(p.stdout.decode("utf-8"))

    def wait_networkidle(self) -> Dict[str, Any]:
        p = self._curl("POST", "/wait", {"load": "networkidle"})
        p.check_returncode()
        return json.loads(p.stdout.decode("utf-8"))

    def snapshot_raw(self) -> Dict[str, Any]:
        # Prefer compact snapshots (smaller/faster; enough for our selectors/parsing).
        p = self._curl("GET", "/snapshot?compact=true")
        p.check_returncode()
        return json.loads(p.stdout.decode("utf-8"))

    def screenshot_to(self, path: Path) -> None:
        p = self._curl("GET", "/screenshot", out_file=path)
        p.check_returncode()

    def click(self, selector: str) -> Dict[str, Any]:
        # Prefer snapshot-based click (stable for @e refs). Fallback to legacy /click.
        if selector.startswith("@e"):
            p = self._curl("POST", "/snapshot/click", {"ref": selector})
        else:
            p = self._curl("POST", "/click", {"selector": selector})
        p.check_returncode()
        return json.loads(p.stdout.decode("utf-8"))

    def fill(self, selector: str, text: str) -> Dict[str, Any]:
        # Snapshot fill uses {ref, value}.
        if selector.startswith("@e"):
            p = self._curl("POST", "/snapshot/fill", {"ref": selector, "value": text})
        else:
            # Legacy fallback
            p = self._curl("POST", "/type", {"selector": selector, "text": text})
        p.check_returncode()
        return json.loads(p.stdout.decode("utf-8"))

    def type(self, selector: str, text: str) -> Dict[str, Any]:
        # Back-compat: route to fill()
        return self.fill(selector, text)

    def find(self, by: str, value: str) -> Dict[str, Any]:
        p = self._curl("POST", "/find", {"by": by, "value": value})
        p.check_returncode()
        return json.loads(p.stdout.decode("utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_unique_run_id(outdir: Path, run_id: str) -> str:
    base = run_id
    suffix = 1
    while True:
        candidates = [
            outdir / f"{run_id}.prompt.txt",
            outdir / f"{run_id}.response.txt",
            outdir / f"{run_id}.snapshot.json",
            outdir / f"{run_id}.meta.json",
            outdir / f"{run_id}.screenshot.png",
        ]
        if not any(p.exists() for p in candidates):
            return run_id
        suffix += 1
        run_id = f"{base}-r{suffix:02d}"


def ref_in_line(ln: str) -> Optional[str]:
    m = re.search(r"\[@e\d+\]", ln)
    return m.group(0)[1:-1] if m else None


def find_query_and_submit(snapshot_text: str) -> Tuple[Optional[str], Optional[str]]:
    lines = snapshot_text.splitlines()

    for i, ln in enumerate(lines):
        if 'textbox "Query box"' in ln:
            q = ref_in_line(ln)
            if not q:
                continue
            for ln2 in lines[i : i + 60]:
                if 'button "Submit"' in ln2:
                    sub = ref_in_line(ln2)
                    return q, sub
            return q, None

    # heuristic: last textbox that has a submit soon after
    candidates: list[tuple[int, str]] = []
    for i, ln in enumerate(lines):
        if "- textbox" not in ln:
            continue
        r = ref_in_line(ln)
        if r:
            candidates.append((i, r))

    for i, q in sorted(candidates, key=lambda x: x[0], reverse=True):
        sub = None
        for ln2 in lines[i : i + 80]:
            if 'button "Submit"' in ln2:
                sub = ref_in_line(ln2)
                break
        if sub:
            return q, sub

    return None, None


def find_button_ref(snapshot_text: str, labels: list[str]) -> Optional[str]:
    lines = snapshot_text.splitlines()
    labels_l = [l.lower() for l in labels]
    for ln in lines:
        if " button \"" not in ln:
            continue
        low = ln.lower()
        if not any(lbl in low for lbl in labels_l):
            continue
        r = ref_in_line(ln)
        if r:
            return r
    return None


def find_last_copy_response_button(snapshot_text: str) -> Optional[str]:
    """Return the ref of the last visible Copy button (unanchored)."""
    last = None
    for ln in snapshot_text.splitlines():
        if 'button "Copy model response to clipboard"' in ln:
            r = ref_in_line(ln)
            if r:
                last = r
    return last


def find_copy_button_after_prompt(snapshot_text: str, prompt_text: str) -> Optional[str]:
    """Find the Copy button associated with *this* prompt.

    We locate the last StaticText occurrence of a prompt snippet (first line), then select
    the first Copy button appearing AFTER that point in the snapshot text ordering.

    This avoids copying an older message when chat-clear fails or the transcript is long.
    """
    lines = snapshot_text.splitlines()
    first = (prompt_text.splitlines()[0] if prompt_text else "").strip()
    if not first:
        return None
    # Use a short snippet to be robust to truncation/whitespace.
    snippet = re.sub(r"\s+", " ", first)[:64]
    if not snippet:
        return None

    anchor_idx = None
    for i, ln in enumerate(lines):
        if "StaticText" in ln and snippet.lower() in ln.lower():
            anchor_idx = i

    if anchor_idx is None:
        return None

    for ln in lines[anchor_idx + 1 :]:
        if 'button "Copy model response to clipboard"' in ln:
            r = ref_in_line(ln)
            if r:
                return r
    return None


def extract_response_via_dom_snapshot(prompt_text: str, snapshot_text: str) -> str:
    """DOM/snapshot-based fallback extraction (no clipboard).

    Anchor strategy (validated):
    - Locate the prompt heading (level=3) for this prompt.
    - Collect StaticText nodes after it.
    - Stop at the next action row (Save/Copy/Rate) OR Query box.

    Notes:
    - NotebookLM headings usually contain the first line of the prompt.
    - We match using a normalised first-line snippet to tolerate truncation.

    Returns extracted response text, or "" if not found.
    """
    if not prompt_text or not snapshot_text:
        return ""

    first = (prompt_text.splitlines()[0] if prompt_text else "").strip()
    if not first:
        return ""

    # Normalise and cap snippet to be robust.
    snippet = re.sub(r"\s+", " ", first)[:120].strip().lower()
    if not snippet:
        return ""

    lines = snapshot_text.splitlines()

    def static_value(ln: str) -> Optional[str]:
        m = re.search(r'StaticText "(.*)"', ln)
        if not m:
            return None
        v = re.sub(r"\s+", " ", m.group(1)).strip()
        return v or None

    # Anchor: prefer heading level=3 that contains the snippet.
    anchor_idx = None
    for i, ln in enumerate(lines):
        low = ln.lower()
        if "level=3" in low and "heading \"" in low and snippet in low:
            anchor_idx = i
            break

    # Fallback anchor: StaticText line containing snippet.
    if anchor_idx is None:
        for i, ln in enumerate(lines):
            low = ln.lower()
            if "statictext" in low and snippet in low:
                anchor_idx = i
                break

    if anchor_idx is None:
        return ""

    # End boundary: next action row start (Save/Copy/Rate) or Query box.
    end_idx = None
    for j in range(anchor_idx + 1, len(lines)):
        ln = lines[j]
        if 'button "Save message to a note"' in ln:
            end_idx = j
            break
        if 'button "Copy model response to clipboard"' in ln:
            end_idx = j
            break
        if 'button "Rate response as good"' in ln:
            end_idx = j
            break
        if 'button "Rate response as bad"' in ln:
            end_idx = j
            break
        if 'textbox "Query box"' in ln:
            end_idx = j
            break

    if end_idx is None:
        end_idx = len(lines)

    out: list[str] = []
    for ln in lines[anchor_idx + 1 : end_idx]:
        if "StaticText" not in ln:
            continue
        v = static_value(ln)
        if not v:
            continue
        # Skip any echo of the prompt line.
        if snippet and snippet in v.lower():
            continue
        out.append(v)

    return "\n".join(out).strip()


def crop_chat_column_inplace(png_path: Path) -> bool:
    if Image is None or not png_path.exists():
        return False
    try:
        img = Image.open(png_path)
        w, h = img.size
        x1 = int(round(w * (400.0 / 1332.0)))
        x2 = int(round(w * (1100.0 / 1332.0)))
        x1 = max(0, min(w, x1))
        x2 = max(0, min(w, x2))
        if x2 <= x1 + 10:
            return False
        img.crop((x1, 0, x2, h)).save(png_path)
        return True
    except Exception:
        return False


def pbcopy_text(s: str) -> None:
    try:
        subprocess.run(["pbcopy"], input=(s or "").encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except Exception:
        pass


def pbpaste_text() -> str:
    """Best-effort clipboard capture.

    NotebookLM may write HTML/RTF; we convert via textutil when needed.
    """
    try:
        p = subprocess.run(["pbpaste", "-Prefer", "txt"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        txt = p.stdout.decode("utf-8", errors="replace")
        if txt.strip():
            return txt

        p = subprocess.run(["pbpaste", "-Prefer", "html"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        html = p.stdout
        if html and html.strip():
            t = subprocess.run(["/usr/bin/textutil", "-convert", "txt", "-stdin", "-stdout"], input=html, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            out = t.stdout.decode("utf-8", errors="replace")
            if out.strip():
                return out

        p = subprocess.run(["pbpaste", "-Prefer", "rtf"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        rtf = p.stdout
        if rtf and rtf.strip():
            t = subprocess.run(["/usr/bin/textutil", "-convert", "txt", "-stdin", "-stdout"], input=rtf, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            out = t.stdout.decode("utf-8", errors="replace")
            if out.strip():
                return out

        p = subprocess.run(["pbpaste"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return p.stdout.decode("utf-8", errors="replace")
    except Exception:
        return ""


def find_action_ref(snapshot_text: str, labels: list[str]) -> Optional[str]:
    """Find a clickable element (menuitem/button/link) containing any label."""
    lines = snapshot_text.splitlines()
    labels_l = [l.lower() for l in labels]
    for ln in lines:
        low = ln.lower()
        if not (" menuitem \"" in ln or " button \"" in ln or " link \"" in ln):
            continue
        if not any(lbl in low for lbl in labels_l):
            continue
        r = ref_in_line(ln)
        if r:
            return r
    return None


def clear_chat_history(t: Tandem) -> None:
    snap = t.snapshot_raw().get("snapshot", "")
    chat_opts = find_button_ref(snap, ["Chat options"])
    if not chat_opts:
        raise RuntimeError("chat_options_button_not_found")

    # open menu (and re-open as needed)
    t.click(chat_opts)
    time.sleep(0.9)

    delete_labels = [
        "Delete chat history",
        "Clear chat history",
        "Delete chat",
        "Clear chat",
        "Delete conversation",
        "Clear conversation",
        "Delete history",
        "Clear history",
        "Delete",
        "Clear",
    ]

    ref = None
    for _ in range(14):
        s2 = t.snapshot_raw().get("snapshot", "")

        # 1) try snapshot parsing first (often works even when /find doesn't see overlays)
        ref = find_action_ref(s2, delete_labels)
        if ref:
            break

        # 2) fallback: use /find (more robust when it works)
        for needle in delete_labels:
            try:
                f = t.find("text", needle)
                if f.get("found") and f.get("ref"):
                    ref = f["ref"]
                    break
            except Exception:
                pass
        if ref:
            break

        # re-open menu in case it closed
        t.click(chat_opts)
        time.sleep(1.0)

    if not ref:
        raise RuntimeError("delete_chat_history_menuitem_not_found")

    t.click(ref)
    time.sleep(0.9)

    s3 = t.snapshot_raw().get("snapshot", "")
    confirm = find_button_ref(s3, ["Delete", "Clear"])
    if confirm:
        t.click(confirm)
        time.sleep(1.0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt-number", type=int, required=True)
    ap.add_argument("--prompt-name", type=str, required=True)
    ap.add_argument("--prompt-text", type=str, required=True)
    ap.add_argument("--notebook-url", type=str, default=None)
    ap.add_argument("--outdir", type=str, default="/Users/igorsilva/clawd/tmp/notebooklm-runs")
    ap.add_argument("--base", type=str, default=BASE_DEFAULT)
    ap.add_argument("--token-path", type=str, default=TOKEN_PATH_DEFAULT)
    ap.add_argument("--max-checks", type=int, default=240)
    ap.add_argument("--sleep-seconds", type=float, default=2.0)
    ap.add_argument("--click-type-retries", type=int, default=3)
    ap.add_argument("--log-dir", type=str, default=LOG_DIR_DEFAULT)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    log_path = Path(args.log_dir) / ("fetcher-clipboard-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d") + ".log")

    token = Path(args.token_path).read_text(encoding="utf-8").strip()
    t = Tandem(base=args.base, token=token)

    slug = slugify(args.prompt_name)
    run_id = ensure_unique_run_id(outdir, local_run_id(args.prompt_number, slug))

    prompt_path = outdir / f"{run_id}.prompt.txt"
    response_path = outdir / f"{run_id}.response.txt"
    snapshot_path = outdir / f"{run_id}.snapshot.json"
    screenshot_path = outdir / f"{run_id}.screenshot.png"
    meta_path = outdir / f"{run_id}.meta.json"

    meta: Dict[str, Any] = {
        "schema": "notebooklm.fetch.run.v2",
        "run_id": run_id,
        "created_at": utc_now_iso(),
        "prompt_number": args.prompt_number,
        "prompt_name": args.prompt_name,
        "slug": slug,
        "notebook_url": args.notebook_url,
        "tandem": {"base_url": args.base},
        "selectors": {"query_box": None, "submit": None, "copy_response": None},
        "checks": {"max_checks": args.max_checks, "sleep_seconds": args.sleep_seconds, "attempted": 0},
        "result": {"status": None, "partial": False, "error": None, "extraction_mode": None},
        "recovery": {
            "state": "NOT_STARTED",
            "attempts": [],
            "budget": {
                "total_attempts_used": 0,
                "refresh_used": 0,
                "chat_clear_used": 0
            },
            "recommended_resume_action": None,
            "recommended_command": None
        },
        "artifacts": {
            "prompt_txt": str(prompt_path),
            "response_txt": str(response_path),
            "snapshot_json": str(snapshot_path),
            "screenshot_png": str(screenshot_path),
            "meta_json": str(meta_path),
        },
    }

    write_text(prompt_path, args.prompt_text)
    log_line(log_path, args.prompt_number, "run_id", "ok", f"run_id={run_id}")

    try:
        st = t.status()
        meta["tandem"].update({"url": st.get("url"), "title": st.get("title"), "ready": st.get("ready"), "loading": st.get("loading")})
    except Exception as e:
        meta["result"].update({"status": "blocked", "partial": False, "error": f"tandem_status_failed: {e}"})
        write_json(meta_path, meta)
        update_or_append_err(
            pattern_key="harden.tandem.connection_failure",
            summary="Tandem connection failure: /status failed (NotebookLM fetcher cannot reach Tandem).",
            error_lines=[f"tandem_status_failed: {e}"],
            context_lines=[
                f"Operation: notebooklm-fetcher fetch_clipboard.py --prompt-number {args.prompt_number}",
                f"Tandem base: {args.base}",
                f"Notebook URL: {args.notebook_url or 'none'}",
                f"Run ID: {run_id}",
                f"Log: {log_path}",
            ],
            suggested_fix_lines=[
                "Check Tandem server is running and reachable at base URL",
                "Verify ~/.tandem/api-token is valid",
                "Restart OpenClaw gateway + Tandem if needed",
            ],
        )
        return 2

    if args.notebook_url:
        try:
            t.navigate(args.notebook_url)
            t.wait_networkidle()
        except Exception as e:
            meta["result"].update({"status": "error", "partial": False, "error": f"navigate_failed: {e}"})
            write_json(meta_path, meta)
            update_or_append_err(
                pattern_key="harden.notebooklm.response_timeout_or_partial",
                summary="NotebookLM fetcher navigation/network idle wait failed (timeout or partial load).",
                error_lines=[f"navigate_failed: {e}"],
                context_lines=[
                    f"Operation: notebooklm-fetcher fetch_clipboard.py --prompt-number {args.prompt_number}",
                    f"Notebook URL: {args.notebook_url}",
                    f"Run ID: {run_id}",
                    f"Artifacts: {meta_path}",
                ],
                suggested_fix_lines=[
                    "Increase networkidle wait tolerance or switch to element-based readiness",
                    "Retry navigate once before failing",
                    "Capture screenshot+snapshot for diagnosis",
                ],
            )
            return 3

    # Clear chat for isolation (best-effort). If it fails, continue and rely on response anchoring.
    # IMPORTANT: do NOT mark the run partial just because this UI action isn't available.
    # Only mark partial when response extraction/copying fails.
    try:
        clear_chat_history(t)
        log_line(log_path, args.prompt_number, "clear_chat_history", "ok", "")
    except Exception as e:
        # Keep going; record as warning for diagnosis.
        if meta.get("result") and meta["result"].get("error") is None:
            meta["result"].update({"error": f"clear_chat_history_failed: {e}"})
        log_line(log_path, args.prompt_number, "clear_chat_history", "warn", f"error={e}")

    snap0 = t.snapshot_raw()
    write_json(snapshot_path, snap0)

    q, sub = find_query_and_submit(snap0.get("snapshot", ""))
    meta["selectors"].update({"query_box": q, "submit": sub})
    if not q or not sub:
        meta["result"].update({"status": "blocked", "partial": False, "error": "selectors_not_found"})
        write_json(meta_path, meta)
        return 5

    # Send prompt
    ok_sent = False
    last_err = None
    for attempt in range(1, args.click_type_retries + 1):
        try:
            t.click(q)
            # More reliable than keystroke typing: fill textbox via Tandem snapshot API.
            t.fill(q, args.prompt_text)
            # click submit as primary
            t.click(sub)
            ok_sent = True
            break
        except Exception as e:
            last_err = str(e)
            time.sleep(0.6 * attempt)

    # Submission evidence gate: avoid waiting forever in "home" state.
    # We expect either the prompt snippet to appear in the transcript OR any sign of generation/response controls.
    submitted = False
    if ok_sent:
        first = (args.prompt_text.splitlines()[0] if args.prompt_text else "").strip()
        snippet = re.sub(r"\s+", " ", first)[:64].lower() if first else ""
        for _ in range(8):  # ~8 seconds max (short gate)
            try:
                s_gate = t.snapshot_raw().get("snapshot", "")
            except Exception:
                time.sleep(1.0)
                continue
            low = s_gate.lower()
            if snippet and snippet in low:
                submitted = True
                break
            # weak signals that something happened
            if "stop" in low or "generating" in low or "thinking" in low:
                submitted = True
                break
            time.sleep(1.0)

        if not submitted:
            # Refresh once and retry submission
            try:
                t.navigate(args.notebook_url)
                t.wait_networkidle()
            except Exception:
                pass
            snap_retry = t.snapshot_raw()
            q2, sub2 = find_query_and_submit(snap_retry.get("snapshot", ""))
            if q2 and sub2:
                q, sub = q2, sub2
                meta["selectors"].update({"query_box": q, "submit": sub})
                try:
                    t.click(q)
                    t.type(q, args.prompt_text)
                    t.click(sub)
                except Exception as e:
                    last_err = str(e)

                # Re-check evidence after retry submission.
                submitted = False
                for _ in range(8):
                    try:
                        s_gate = t.snapshot_raw().get("snapshot", "")
                    except Exception:
                        time.sleep(1.0)
                        continue
                    low = s_gate.lower()
                    if snippet and snippet in low:
                        submitted = True
                        break
                    if "stop" in low or "generating" in low or "thinking" in low:
                        submitted = True
                        break
                    time.sleep(1.0)

    if ok_sent and not submitted:
        meta["result"].update({"status": "blocked", "partial": False, "error": "submit_no_evidence"})
        write_json(meta_path, meta)
        return 6

    if not ok_sent:
        meta["result"].update({"status": "blocked", "partial": False, "error": f"click_type_failed: {last_err}"})
        write_json(meta_path, meta)
        return 6

    # Wait for the Copy button *after this prompt* (anchored), to avoid copying an older response.
    copy_ref = None
    final_snap = None
    stable_hits = 0
    last_seen = None
    meta["recovery"]["state"] = "WAITING_FOR_RESPONSE"

    def record_recovery(step: str, outcome: str) -> None:
        meta["recovery"]["budget"]["total_attempts_used"] += 1
        meta["recovery"]["attempts"].append({
            "step": step,
            "started_at": utc_now_iso(),
            "ended_at": utc_now_iso(),
            "outcome": outcome,
        })

    def probe_copy(max_checks: int) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
        local_copy_ref = None
        local_final_snap = None
        local_stable_hits = 0
        local_last_seen = None
        for i in range(1, max_checks + 1):
            meta["checks"]["attempted"] += 1
            try:
                t.wait_networkidle()
            except Exception:
                pass
            local_final_snap = t.snapshot_raw()
            s_txt = local_final_snap.get("snapshot", "")
            cur = find_copy_button_after_prompt(s_txt, args.prompt_text)
            if cur:
                if cur == local_last_seen:
                    local_stable_hits += 1
                else:
                    local_stable_hits = 0
                    local_last_seen = cur
                if local_stable_hits >= 1:
                    local_copy_ref = cur
                    break
            time.sleep(args.sleep_seconds)
        return local_copy_ref, local_final_snap

    copy_ref, final_snap = probe_copy(args.max_checks)

    # Self-heal step 1: re-snapshot once if copy button is missing.
    if not copy_ref:
        meta["recovery"]["state"] = "RECOVERY_ATTEMPT"
        record_recovery("re-snapshot", "retry_copy_detection")
        copy_ref, final_snap = probe_copy(max(3, min(8, args.max_checks // 2 or 3)))

    # Self-heal step 2: soft refresh once if still missing.
    if not copy_ref and args.notebook_url:
        try:
            meta["recovery"]["budget"]["refresh_used"] += 1
            record_recovery("soft-refresh", "navigate_and_retry")
            t.navigate(args.notebook_url)
            t.wait_networkidle()
            copy_ref, final_snap = probe_copy(max(3, min(8, args.max_checks // 2 or 3)))
        except Exception as e:
            record_recovery("soft-refresh", f"failed:{e}")

    if final_snap is None:
        final_snap = snap0

    meta["selectors"]["copy_response"] = copy_ref
    write_json(snapshot_path, final_snap)

    # Debug screenshot
    try:
        t.screenshot_to(screenshot_path)
        crop_chat_column_inplace(screenshot_path)
    except Exception:
        pass

    partial = False
    raw = ""
    if not copy_ref:
        partial = True
        meta["recovery"]["state"] = "BLOCKED_RECOVERABLE"
        meta["recovery"]["recommended_resume_action"] = "resume-current-prompt"
        meta["result"]["error"] = "copy_button_not_found"
        update_or_append_err(
            pattern_key="harden.notebooklm_copy_button_selector_drift",
            summary="NotebookLM fetcher failed to locate the Copy model response button and produced partial output.",
            error_lines=["copy_button_not_found"],
            context_lines=[
                f"Operation: notebooklm-fetcher fetch_clipboard.py --prompt-number {args.prompt_number}",
                f"Notebook URL: {args.notebook_url or 'none'}",
                f"Run ID: {run_id}",
                f"Max checks: {args.max_checks} (timeout waiting for Copy button)",
                f"Artifacts: {meta_path}",
            ],
            suggested_fix_lines=[
                "Update selector strategy (prefer role/name-based queries over brittle snapshot ordering)",
                "Add fallback UI path to copy (context menu / alternate copy affordance)",
                "Fail hard (exit non-zero) when Copy button is missing to stop downstream placeholder propagation",
            ],
        )
    else:
        # Sentinel-based capture to prevent re-saving stale clipboard text.
        sentinel = f"__NOTEBOOKLM_CLIPBOARD_SENTINEL__:{run_id}__"
        pbcopy_text(sentinel)
        time.sleep(0.15)

        try:
            for attempt in range(1, 7):
                # re-snapshot and re-anchor occasionally (DOM can re-render)
                if attempt in (3, 5):
                    try:
                        s_txt = t.snapshot_raw().get("snapshot", "")
                        new_ref = find_copy_button_after_prompt(s_txt, args.prompt_text) or copy_ref
                        copy_ref = new_ref
                        meta["selectors"]["copy_response"] = copy_ref
                    except Exception:
                        pass

                t.click(copy_ref)
                time.sleep(0.85)
                raw = pbpaste_text().strip()

                # TEST HOOK (off by default): force clipboard to be treated as empty
                # so we can validate DOM fallback deterministically.
                if os.environ.get("NOTEBOOKLM_FORCE_EMPTY_CLIPBOARD") == "1":
                    raw = ""

                # accept only if it changed from sentinel and is non-empty
                if raw and sentinel not in raw:
                    break
                time.sleep(0.5 * attempt)

            if not raw or sentinel in raw:
                raw = ""
                partial = True
                meta["result"]["error"] = "clipboard_stale_or_empty"
                update_or_append_err(
                    pattern_key="harden.notebooklm.placeholder_output_detected",
                    summary="NotebookLM fetcher detected placeholder/empty output after clicking Copy (clipboard stale or empty).",
                    error_lines=["clipboard_stale_or_empty"],
                    context_lines=[
                        f"Operation: notebooklm-fetcher fetch_clipboard.py --prompt-number {args.prompt_number}",
                        f"Notebook URL: {args.notebook_url or 'none'}",
                        f"Run ID: {run_id}",
                        f"Copy ref: {copy_ref or 'none'}",
                        f"Artifacts: {meta_path}",
                    ],
                    suggested_fix_lines=[
                        "Increase retry/backoff around clipboard capture",
                        "Capture and persist raw clipboard types (txt/html/rtf) for diagnosis",
                        "Hard-fail when clipboard is stale/empty to prevent downstream placeholder propagation",
                    ],
                )
        except Exception as e:
            partial = True
            meta["result"]["error"] = f"clipboard_capture_failed: {e}"
            update_or_append_err(
                pattern_key="harden.notebooklm.clipboard_capture_failed",
                summary="NotebookLM fetcher failed during clipboard capture after clicking Copy.",
                error_lines=[f"clipboard_capture_failed: {e}"],
                context_lines=[
                    f"Operation: notebooklm-fetcher fetch_clipboard.py --prompt-number {args.prompt_number}",
                    f"Notebook URL: {args.notebook_url or 'none'}",
                    f"Run ID: {run_id}",
                    f"Copy ref: {copy_ref or 'none'}",
                    f"Artifacts: {meta_path}",
                ],
                suggested_fix_lines=[
                    "Check pbpaste/pbcopy availability and permissions",
                    "Add screenshot+snapshot capture at point of failure",
                    "Consider alternative extraction path if clipboard is unreliable",
                ],
            )

    # DOM/snapshot fallback if clipboard capture failed/stale/empty or Copy button is missing.
    # Strategy:
    #   1) Try to extract the model response from the DOM snapshot anchored on the prompt text.
    #   2) If the prompt isn't present in the snapshot (e.g. prompt send failed or UI scrolled),
    #      do NOT guess — keep partial.
    if partial and not raw and meta["result"].get("error") in (
        "clipboard_stale_or_empty",
        "clipboard_capture_failed",
        "placeholder_output_detected",
        "copy_button_not_found",
    ):
        try:
            snap_for_dom = t.snapshot_raw().get("snapshot", "")

            # Guard: only attempt DOM extraction if we can see the prompt anchor.
            first = (args.prompt_text.splitlines()[0] if args.prompt_text else "").strip()
            snippet = re.sub(r"\s+", " ", first)[:64].lower() if first else ""
            if snippet and any(("statictext" in ln.lower() and snippet in ln.lower()) for ln in snap_for_dom.splitlines()):
                dom_txt = extract_response_via_dom_snapshot(args.prompt_text, snap_for_dom)
            else:
                dom_txt = ""

            # Reject obvious UI chrome captures.
            ui_chrome = (
                re.search(r"\bNotebookLM can be inaccurate\b", dom_txt)
                or re.search(r"\bAudio Overview\b", dom_txt)
                or re.search(r"\bSlide deck\b", dom_txt)
                or re.search(r"\bMind Map\b", dom_txt)
            )

            if dom_txt and not ui_chrome and not re.search(r"\bplaceholder\b", dom_txt, flags=re.I):
                raw = dom_txt
                partial = False
                meta["result"]["error"] = None
                meta["result"]["extraction_mode"] = "dom"
                meta["recovery"]["state"] = "DONE"
            else:
                partial = True
                meta["result"]["error"] = meta["result"].get("error") or "dom_extract_failed"
        except Exception:
            pass

    # Placeholder output detection (defensive): treat obvious placeholders as failure.
    if raw and re.search(r"\bplaceholder\b", raw, flags=re.I):
        partial = True
        meta["result"]["error"] = "placeholder_output_detected"
        update_or_append_err(
            pattern_key="harden.notebooklm.placeholder_output_detected",
            summary="NotebookLM fetcher detected placeholder output in captured response.",
            error_lines=["placeholder_output_detected"],
            context_lines=[
                f"Operation: notebooklm-fetcher fetch_clipboard.py --prompt-number {args.prompt_number}",
                f"Notebook URL: {args.notebook_url or 'none'}",
                f"Run ID: {run_id}",
                f"Artifacts: {meta_path}",
            ],
            suggested_fix_lines=[
                "Treat placeholder markers as hard failures (exit non-zero) to stop downstream processing",
                "Capture screenshot+snapshot at failure point for selector/debug",
            ],
        )
        raw = ""

    if raw and meta["result"].get("extraction_mode") is None:
        meta["result"]["extraction_mode"] = "clipboard"
        meta["recovery"]["state"] = "DONE"

    if raw:
        write_text(response_path, raw + "\n")
    else:
        partial = True
        write_text(response_path, "")

    meta["result"].update({"status": "blocked_recoverable" if partial else "ok", "partial": partial})
    if partial and meta["recovery"].get("recommended_resume_action") is None:
        meta["recovery"]["state"] = "BLOCKED_RECOVERABLE"
        meta["recovery"]["recommended_resume_action"] = "resume-current-prompt"
        meta["recovery"]["recommended_command"] = "Resume the existing notebooklm-runner child run for this prompt."
    write_json(meta_path, meta)

    return 0 if not partial else 1


if __name__ == "__main__":
    raise SystemExit(main())
