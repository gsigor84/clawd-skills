#!/opt/anaconda3/bin/python3
"""NotebookLM fetcher (Tandem) — send one prompt, save raw artifacts.

Writes per run:
- {RUN_ID}.prompt.txt
- {RUN_ID}.response.txt   (clipboard-captured raw response)
- {RUN_ID}.snapshot.json  (debug; not used for extraction)
- {RUN_ID}.screenshot.png (debug)
- {RUN_ID}.meta.json

Primary extraction path: click "Copy model response to clipboard" and capture via pbpaste.
No OCR. No snapshot parsing for text extraction.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Optional image crop dependencies
try:
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover
    Image = None


LOG_DIR_DEFAULT = "/Users/igorsilva/clawd/tmp/logs"


BASE_DEFAULT = "http://127.0.0.1:8765"
TOKEN_PATH_DEFAULT = os.path.expanduser("~/.tandem/api-token")


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def log_line(log_path: Path, prompt_number: int, event: str, status: str, detail: str = "") -> None:
    ts = utc_now_iso().replace("+00:00", "Z")
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
        cmd = [
            "curl",
            "-sS",
            "-H",
            f"Authorization: Bearer {self.token}",
        ]
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
        p = self._curl("GET", "/snapshot")
        p.check_returncode()
        return json.loads(p.stdout.decode("utf-8"))

    def screenshot_to(self, path: Path) -> None:
        p = self._curl("GET", "/screenshot", out_file=path)
        p.check_returncode()

    def click(self, selector: str) -> Dict[str, Any]:
        p = self._curl("POST", "/click", {"selector": selector})
        p.check_returncode()
        return json.loads(p.stdout.decode("utf-8"))

    def type(self, selector: str, text: str) -> Dict[str, Any]:
        p = self._curl("POST", "/type", {"selector": selector, "text": text})
        p.check_returncode()
        return json.loads(p.stdout.decode("utf-8"))

    def scroll(self, delta_y: int = 800) -> Dict[str, Any]:
        """Scroll the page.

        Note: This is page-level scroll. For virtualized chat panes, we approximate
        full capture by scrolling in both directions and snapshotting.
        """
        p = self._curl("POST", "/scroll", {"deltaY": int(delta_y)})
        p.check_returncode()
        return json.loads(p.stdout.decode("utf-8"))

    def find(self, by: str, value: str) -> Dict[str, Any]:
        p = self._curl("POST", "/find", {"by": by, "value": value})
        p.check_returncode()
        return json.loads(p.stdout.decode("utf-8"))


def find_query_and_submit(snapshot_text: str) -> Tuple[Optional[str], Optional[str]]:
    """Best-effort locate the chat query textbox and its Submit button.

    NotebookLM's accessibility labels can vary slightly across renders.
    Strategy:
    - Prefer an explicit textbox labelled "Query box".
    - Otherwise, pick the last reasonable textbox in the page (excluding Sources search/title box)
      for which a "Submit" button appears shortly after.
    """
    lines = snapshot_text.splitlines()

    def ref_in_line(ln: str) -> Optional[str]:
        m = re.search(r"\[@e\d+\]", ln)
        return m.group(0)[1:-1] if m else None

    # 1) Exact match first
    for i, ln in enumerate(lines):
        if 'textbox "Query box"' in ln:
            q = ref_in_line(ln)
            if not q:
                continue
            # find submit nearby
            for ln2 in lines[i : i + 60]:
                if 'button "Submit"' in ln2:
                    sub = ref_in_line(ln2)
                    return q, sub
            return q, None

    # 2) Heuristic: candidate textboxes that look like the chat input
    candidates: list[tuple[int, str]] = []
    for i, ln in enumerate(lines):
        if "- textbox" not in ln:
            continue
        low = ln.lower()
        # Exclude notebook title input and source discovery box
        if 'discover sources based on the inputted query' in low:
            continue
        if 'value="building ai agent platforms"' in low:
            continue
        # Prefer things that look like the chat input
        if 'textbox "query box"' in low or 'query box' in low:
            r = ref_in_line(ln)
            if r:
                candidates.append((i, r))
            continue
        # Fallback: any unnamed textbox near a Submit button soon after
        r = ref_in_line(ln)
        if r:
            candidates.append((i, r))

    # walk from bottom (chat input is usually near bottom)
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
    """Find a button element handle by its accessible name containing any label."""
    lines = snapshot_text.splitlines()
    labels_l = [l.lower() for l in labels]
    for ln in lines:
        if " button \"" not in ln:
            continue
        low = ln.lower()
        if not any(lbl in low for lbl in labels_l):
            continue
        m = re.search(r"\[@e\d+\]", ln)
        if m:
            return m.group(0)[1:-1]
    return None


def find_menuitem_ref(snapshot_text: str, labels: list[str]) -> Optional[str]:
    """Find a menuitem element handle by its accessible name containing any label."""
    lines = snapshot_text.splitlines()
    labels_l = [l.lower() for l in labels]
    for ln in lines:
        if " menuitem \"" not in ln:
            continue
        low = ln.lower()
        if not any(lbl in low for lbl in labels_l):
            continue
        m = re.search(r"\[@e\d+\]", ln)
        if m:
            return m.group(0)[1:-1]
    return None


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
        m = re.search(r"\[@e\d+\]", ln)
        if m:
            return m.group(0)[1:-1]
    return None


def clear_chat_history(t: Tandem, log_path: Path, prompt_number: int) -> None:
    """Clear NotebookLM chat history via: Chat options → Delete chat history → Delete.

    This is the only reliable 'new chat' mechanism exposed in the accessibility tree.
    Raises on failure.
    """
    snap = t.snapshot_raw()
    s_txt = snap.get("snapshot", "")

    chat_opts = find_button_ref(s_txt, ["Chat options"])
    if not chat_opts:
        raise RuntimeError("chat_options_button_not_found")

    t.click(chat_opts)
    log_line(log_path, prompt_number, "chat_options", "ok", f"ref={chat_opts}")
    time.sleep(0.8)

    # menu may take a moment to render; retry a few times
    del_item = None
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
    for _ in range(8):
        snap2 = t.snapshot_raw()
        s2 = snap2.get("snapshot", "")
        del_item = find_action_ref(s2, delete_labels)
        if del_item:
            break
        # fallback: use /find (more robust than snapshot parsing for overlays)
        for needle in delete_labels:
            try:
                found = t.find("text", needle)
                if found.get("found") and found.get("ref"):
                    del_item = found["ref"]
                    break
            except Exception:
                pass
        if del_item:
            break
        # click chat options again to re-open if it closed
        t.click(chat_opts)
        time.sleep(0.9)

    if not del_item:
        raise RuntimeError("delete_chat_history_menuitem_not_found")

    t.click(del_item)
    log_line(log_path, prompt_number, "delete_chat_history", "ok", f"ref={del_item}")
    time.sleep(0.8)

    # Confirm dialog (may not appear if chat is already empty or UI short-circuits)
    snap3 = t.snapshot_raw()
    s3 = snap3.get("snapshot", "")

    # If the UI is already back to normal and Query box exists, treat as success.
    q, sub = find_query_and_submit(s3)
    if q and sub and chat_looks_empty(s3):
        log_line(log_path, prompt_number, "delete_confirm", "ok", "skipped_confirm_dialog")
        return

    confirm = find_button_ref(s3, ["Delete", "Clear"])
    if not confirm:
        # fallback: use /find
        try:
            found = t.find("text", "Delete")
            if found.get("found") and found.get("ref"):
                confirm = found["ref"]
        except Exception:
            pass

    if not confirm:
        raise RuntimeError("delete_confirm_button_not_found")

    t.click(confirm)
    log_line(log_path, prompt_number, "delete_confirm", "ok", f"ref={confirm}")

    # Wait for modal to disappear; otherwise Query box won't be discoverable.
    for _ in range(20):
        try:
            t.wait_networkidle()
        except Exception:
            pass
        time.sleep(0.5)
        s = t.snapshot_raw().get("snapshot", "")
        if "dialog \"Delete chat history for this notebook\"" in s:
            continue
        # also require that the query box exists again
        q, sub = find_query_and_submit(s)
        if q and sub:
            break

    # Optional confirmation snapshot
    snap4 = t.snapshot_raw()
    if chat_looks_empty(snap4.get("snapshot", "")):
        log_line(log_path, prompt_number, "confirm_empty", "ok", "")
    else:
        log_line(log_path, prompt_number, "confirm_empty", "fail", "chat_not_empty_after_delete")


def chat_looks_empty(snapshot_text: str) -> bool:
    """Heuristic: chat is empty if it doesn't show prior message markers."""
    low = snapshot_text.lower()
    # Presence of saved-chat markers typically means old content exists
    if "save to note" in low:
        return False
    if "today" in low and "•" in snapshot_text:
        return False
    # If lots of numbered Q/A headings exist, it's not empty
    if re.search(r"statictext \"\d+\.\s", snapshot_text, re.I):
        return False
    return True


def snapshot_has_generation_indicator(snapshot_text: str) -> Dict[str, bool]:
    t = snapshot_text.lower()
    return {
        "stop_generating": "stop generating" in t,
        "looking_at_sources": "looking at sources" in t,
        "thinking": "thinking" in t,
    }


def find_last_copy_response_button(snapshot_text: str) -> Optional[str]:
    """Return ref of the last visible "Copy model response to clipboard" button."""
    lines = snapshot_text.splitlines()
    last = None
    for ln in lines:
        if 'button "Copy model response to clipboard"' in ln:
            m = re.search(r"\[@e\d+\]", ln)
            if m:
                last = m.group(0)[1:-1]
    return last


def pbpaste_text() -> str:
    """Best-effort extract clipboard as text.

    NotebookLM may write HTML/RTF; try multiple flavors.
    """
    try:
        # 1) plain text
        p = subprocess.run(["pbpaste", "-Prefer", "txt"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        txt = p.stdout.decode("utf-8", errors="replace")
        if txt.strip():
            return txt

        # 2) HTML → textutil
        p = subprocess.run(["pbpaste", "-Prefer", "html"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        html = p.stdout
        if html and html.strip():
            t = subprocess.run(
                ["/usr/bin/textutil", "-convert", "txt", "-stdin", "-stdout"],
                input=html,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            out = t.stdout.decode("utf-8", errors="replace")
            if out.strip():
                return out

        # 3) RTF → text
        p = subprocess.run(["pbpaste", "-Prefer", "rtf"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        rtf = p.stdout
        if rtf and rtf.strip():
            t = subprocess.run(
                ["/usr/bin/textutil", "-convert", "txt", "-stdin", "-stdout"],
                input=rtf,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            out = t.stdout.decode("utf-8", errors="replace")
            if out.strip():
                return out

        # 4) fallback
        p = subprocess.run(["pbpaste"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return p.stdout.decode("utf-8", errors="replace")
    except Exception:
        return ""


def ensure_unique_run_id(outdir: Path, run_id: str) -> str:
    base = run_id
    suffix = 1
    while True:
        candidates = [
            outdir / f"{run_id}.prompt.txt",
            outdir / f"{run_id}.snapshot.json",
            outdir / f"{run_id}.meta.json",
            outdir / f"{run_id}.screenshot.png",
        ]
        if not any(p.exists() for p in candidates):
            return run_id
        suffix += 1
        run_id = f"{base}-r{suffix:02d}"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def crop_chat_column_inplace(png_path: Path) -> bool:
    """Crop screenshot in-place to center chat column.

    Target crop: x=400..1100 on a 1332px wide viewport; scale proportionally for other widths.
    Returns True if cropped.
    """
    if Image is None:
        return False
    if not png_path.exists():
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
        cropped = img.crop((x1, 0, x2, h))
        cropped.save(png_path)
        return True
    except Exception:
        return False


def merge_snapshot_texts(snapshots: list[dict]) -> str:
    """Merge multiple Tandem snapshot objects into a single snapshot text.

    Strategy: concatenate snapshot strings in order, but keep only the first occurrence
    of each line (preserves citations/StaticText ordering mostly, avoids exact repeats).
    """
    seen = set()
    merged_lines: list[str] = []
    for s in snapshots:
        txt = (s or {}).get("snapshot", "") or ""
        for ln in txt.splitlines():
            if ln in seen:
                continue
            seen.add(ln)
            merged_lines.append(ln)
    return "\n".join(merged_lines).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt-number", type=int, required=True)
    ap.add_argument("--prompt-name", type=str, required=True)
    ap.add_argument("--prompt-text", type=str, required=True)
    ap.add_argument("--notebook-url", type=str, default=None)
    ap.add_argument("--outdir", type=str, default="/Users/igorsilva/clawd/tmp/notebooklm-runs")
    ap.add_argument("--base", type=str, default=BASE_DEFAULT)
    ap.add_argument("--token-path", type=str, default=TOKEN_PATH_DEFAULT)
    ap.add_argument("--max-checks", type=int, default=40)
    ap.add_argument("--sleep-seconds", type=float, default=2.0)
    ap.add_argument("--click-type-retries", type=int, default=3)
    ap.add_argument("--log-dir", type=str, default=LOG_DIR_DEFAULT)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    log_path = Path(args.log_dir) / ("fetcher-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d") + ".log")
    log_line(log_path, args.prompt_number, "start", "ok", f"outdir={outdir}")

    token = Path(args.token_path).read_text(encoding="utf-8").strip()
    t = Tandem(base=args.base, token=token)

    slug = slugify(args.prompt_name)
    run_id = ensure_unique_run_id(outdir, local_run_id(args.prompt_number, slug))
    log_line(log_path, args.prompt_number, "run_id", "ok", f"run_id={run_id}")

    prompt_path = outdir / f"{run_id}.prompt.txt"
    snapshot_path = outdir / f"{run_id}.snapshot.json"
    screenshot_path = outdir / f"{run_id}.screenshot.png"
    response_path = outdir / f"{run_id}.response.txt"
    meta_path = outdir / f"{run_id}.meta.json"

    meta: Dict[str, Any] = {
        "schema": "notebooklm.fetch.run.v1",
        "run_id": run_id,
        "created_at": utc_now_iso(),
        "prompt_number": args.prompt_number,
        "prompt_name": args.prompt_name,
        "slug": slug,
        "notebook_url": args.notebook_url,
        "tandem": {"base_url": args.base},
        "selectors": {"query_box": None, "submit": None},
        "checks": {
            "max_checks": args.max_checks,
            "sleep_seconds": args.sleep_seconds,
            "attempted": 0,
            "indicator_stop_generating_seen": False,
            "indicator_looking_at_sources_seen": False,
        },
        "result": {"status": None, "partial": False, "error": None},
        "artifacts": {
            "prompt_txt": str(prompt_path),
            "response_txt": str(response_path),
            "snapshot_json": str(snapshot_path),
            "screenshot_png": str(screenshot_path),
            "meta_json": str(meta_path),
        },
    }

    # Always save prompt first (even if blocked later)
    write_text(prompt_path, args.prompt_text)
    log_line(log_path, args.prompt_number, "save_prompt", "ok", f"path={prompt_path} | chars={len(args.prompt_text)}")

    try:
        st = t.status()
        meta["tandem"].update({"url": st.get("url"), "title": st.get("title"), "ready": st.get("ready"), "loading": st.get("loading")})
        log_line(log_path, args.prompt_number, "status", "ok", f"url={st.get('url','')} | title={st.get('title','')}")
    except Exception as e:
        log_line(log_path, args.prompt_number, "status", "fail", f"error={e}")
        meta["result"].update({"status": "blocked", "partial": False, "error": f"tandem_status_failed: {e}"})
        write_json(meta_path, meta)
        return 2

    try:
        if args.notebook_url:
            log_line(log_path, args.prompt_number, "navigate", "ok", f"url={args.notebook_url}")
            t.navigate(args.notebook_url)
            t.wait_networkidle()
            log_line(log_path, args.prompt_number, "wait_networkidle", "ok", "")
    except Exception as e:
        log_line(log_path, args.prompt_number, "navigate", "fail", f"error={e}")
        meta["result"].update({"status": "error", "partial": False, "error": f"navigate_failed: {e}"})
        # Attempt to save snapshot/screenshot for debugging
        try:
            snap = t.snapshot_raw()
            write_json(snapshot_path, snap)
            t.screenshot_to(screenshot_path)
        except Exception:
            pass
        write_json(meta_path, meta)
        return 3

    # Acquire selectors (and ALWAYS clear chat history first)
    try:
        snap0 = t.snapshot_raw()
        write_json(snapshot_path, snap0)  # pre-action snapshot (overwritten later by final)
        log_line(log_path, args.prompt_number, "snapshot", "ok", f"path={snapshot_path}")

        # Always clear chat history to avoid cross-run contamination and long transcripts.
        # Flow: Chat options → Delete chat history → Delete
        try:
            clear_chat_history(t, log_path, args.prompt_number)
            snap0 = t.snapshot_raw()
            write_json(snapshot_path, snap0)
        except Exception as e:
            log_line(log_path, args.prompt_number, "clear_chat_history", "fail", f"error={e}")
            # Treat as hard blocker: prompts must run in a clean chat.
            meta["result"].update({"status": "blocked", "partial": False, "error": f"clear_chat_history_failed: {e}"})
            try:
                t.screenshot_to(screenshot_path)
            except Exception:
                pass
            write_json(meta_path, meta)
            return 4

        q, sub = find_query_and_submit(snap0.get("snapshot", ""))
        meta["selectors"].update({"query_box": q, "submit": sub})
        if q and sub:
            log_line(log_path, args.prompt_number, "find_input", "ok", f"ref={q}")
            log_line(log_path, args.prompt_number, "find_submit", "ok", f"ref={sub}")
        if not q or not sub:
            log_line(log_path, args.prompt_number, "find_selectors", "fail", "selectors_not_found")
            meta["result"].update({"status": "blocked", "partial": False, "error": "selectors_not_found"})
            # Debug screenshot
            try:
                t.screenshot_to(screenshot_path)
            except Exception:
                pass
            write_json(meta_path, meta)
            return 4
    except Exception as e:
        meta["result"].update({"status": "error", "partial": False, "error": f"snapshot_or_selector_failed: {e}"})
        write_json(meta_path, meta)
        return 5

    q = meta["selectors"]["query_box"]
    sub = meta["selectors"]["submit"]

    # Click/type/submit with retries
    last_err = None
    ok_sent = False
    for attempt in range(1, args.click_type_retries + 1):
        try:
            t.click(q)
            log_line(log_path, args.prompt_number, "click_input", "ok", f"ref={q}")
            t.type(q, args.prompt_text)
            log_line(log_path, args.prompt_number, "type_prompt", "ok", f"{len(args.prompt_text)} chars")
            t.click(sub)
            log_line(log_path, args.prompt_number, "click_submit", "ok", f"ref={sub}")
            ok_sent = True
            break
        except Exception as e:
            last_err = str(e)
            log_line(log_path, args.prompt_number, "send_prompt", "fail", f"attempt={attempt} | error={last_err}")
            time.sleep(0.5 * attempt)

    if not ok_sent:
        meta["result"].update({"status": "blocked", "partial": False, "error": f"click_type_failed: {last_err}"})
        try:
            snap = t.snapshot_raw()
            write_json(snapshot_path, snap)
            t.screenshot_to(screenshot_path)
        except Exception:
            pass
        write_json(meta_path, meta)
        return 6

    # Completion signal: wait for the latest "Copy model response to clipboard" button
    # to appear AND generation indicators to be absent.
    partial = False
    final_snap = None
    copy_ref = None

    for i in range(1, args.max_checks + 1):
        meta["checks"]["attempted"] = i
        try:
            t.wait_networkidle()
        except Exception:
            pass

        try:
            final_snap = t.snapshot_raw()
        except Exception as e:
            log_line(log_path, args.prompt_number, "wait_complete", "fail", f"checks={i} | error={e}")
            meta["result"].update({"status": "error", "partial": True, "error": f"snapshot_failed_midloop: {e}"})
            partial = True
            break

        s_txt = final_snap.get("snapshot", "")
        ind = snapshot_has_generation_indicator(s_txt)
        if ind["stop_generating"]:
            meta["checks"]["indicator_stop_generating_seen"] = True
        if ind["looking_at_sources"]:
            meta["checks"]["indicator_looking_at_sources_seen"] = True

        copy_ref = find_last_copy_response_button(s_txt)

        if copy_ref and not (ind["stop_generating"] or ind["looking_at_sources"] or ind["thinking"]):
            log_line(log_path, args.prompt_number, "wait_copy_button", "ok", f"checks={i} | ref={copy_ref}")
            break

        time.sleep(args.sleep_seconds)

    if final_snap is None:
        final_snap = snap0

    if not copy_ref:
        partial = True
        log_line(log_path, args.prompt_number, "wait_copy_button", "fail", f"checks={meta['checks']['attempted']} | ref_not_found")

    # Save debug snapshot
    write_json(snapshot_path, final_snap)

    # Capture screenshot (debug only) and crop at capture time
    try:
        t.screenshot_to(screenshot_path)
        cropped = crop_chat_column_inplace(screenshot_path)
        log_line(log_path, args.prompt_number, "crop_screenshot", "ok" if cropped else "skip", f"path={screenshot_path}")
    except Exception as e:
        meta["result"]["error"] = (meta["result"].get("error") or "") + f" | screenshot_failed: {e}"

    # Click Copy → pbpaste → save response
    raw = ""
    if copy_ref:
        try:
            t.click(copy_ref)
            log_line(log_path, args.prompt_number, "click_copy", "ok", f"ref={copy_ref}")
            time.sleep(0.4)
            raw = pbpaste_text().strip()
            # If clipboard propagation is slow, retry a couple times
            if not raw:
                time.sleep(0.8)
                raw = pbpaste_text().strip()
            if not raw:
                # try clicking again once
                t.click(copy_ref)
                time.sleep(0.6)
                raw = pbpaste_text().strip()
        except Exception as e:
            partial = True
            meta["result"]["error"] = (meta["result"].get("error") or "") + f" | copy_or_pbpaste_failed: {e}"
            log_line(log_path, args.prompt_number, "clipboard_capture", "fail", f"error={e}")

    if raw:
        write_text(response_path, raw + "\n")
        log_line(log_path, args.prompt_number, "save_response", "ok", f"path={response_path} | chars={len(raw)}")
    else:
        partial = True
        write_text(response_path, "")
        log_line(log_path, args.prompt_number, "save_response", "fail", f"path={response_path} | empty_clipboard")

    meta["result"].update({"status": "partial" if partial else "ok", "partial": partial})
    write_json(meta_path, meta)
    log_line(log_path, args.prompt_number, "save_artifacts", "ok", f"run_id={run_id} | status={meta['result']['status']}")

    return 0 if not partial else 1


if __name__ == "__main__":
    raise SystemExit(main())
