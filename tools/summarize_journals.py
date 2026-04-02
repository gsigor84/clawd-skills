#!/opt/anaconda3/bin/python3
"""summarize_journals.py

Reads Adam's Nietzschean journal and synthesizes updated identity fields,
then writes them back into adam_identity.json.

Steps:
1) Read all entries from ~/clawd/adam_nietzsche_journal.md
2) Call OpenClaw primary model (MiniMax provider configured in ~/.openclaw/openclaw.json)
   to extract:
     - current_weaknesses (3-5)
     - strengthening_goals (3-5)
     - biography (1 paragraph)
     - credo (1-2 sentences)
   Output JSON only.
3) Update ~/clawd/adam_identity.json with those fields + last_synthesized (YYYY-MM-DD)

Notes:
- Uses the MiniMax provider settings already configured in ~/.openclaw/openclaw.json.
- Does NOT require env MINIMAX_API_KEY if apiKey is present in openclaw.json.

Usage:
  /opt/anaconda3/bin/python3 ~/clawd/tools/summarize_journals.py --dry-run
  /opt/anaconda3/bin/python3 ~/clawd/tools/summarize_journals.py
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import urllib.request
import urllib.error


WORKSPACE = Path("/Users/igorsilva/clawd")
JOURNAL_PATH = WORKSPACE / "adam_nietzsche_journal.md"
IDENTITY_PATH = WORKSPACE / "adam_identity.json"
OPENCLAW_CFG_PATH = Path("/Users/igorsilva/.openclaw/openclaw.json")


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _load_json(p: Path) -> Dict[str, Any]:
    return json.loads(_read_text(p))


def _dump_json(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


@dataclass
class MiniMaxConfig:
    base_url: str
    api_key: str
    model_id: str
    api: str


def _load_minimax_config() -> MiniMaxConfig:
    cfg = _load_json(OPENCLAW_CFG_PATH)
    mm = cfg.get("models", {}).get("providers", {}).get("minimax", {})

    base_url = mm.get("baseUrl")
    api_key = mm.get("apiKey") or os.environ.get("MINIMAX_API_KEY") or ""
    api = mm.get("api")

    models = mm.get("models") or []
    model_id = (models[0].get("id") if models else None) or "MiniMax-M2.5"

    missing = [k for k, v in [("baseUrl", base_url), ("apiKey", api_key), ("api", api)] if not v]
    if missing:
        raise RuntimeError(f"MiniMax config missing: {', '.join(missing)}")

    return MiniMaxConfig(base_url=base_url, api_key=api_key, model_id=model_id, api=api)


def _http_json(url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        return json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        # Re-raise with response body attached for diagnosis.
        raise RuntimeError(f"http_error:{e.code}:{body}")


def _extract_json_only(text: str) -> Dict[str, Any]:
    # allow model to wrap JSON in code fences; extract the first {...} block
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", text)
        text = re.sub(r"\n```\s*$", "", text)
        text = text.strip()

    # If it's already valid JSON
    try:
        return json.loads(text)
    except Exception:
        pass

    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("model_output_not_json")
    return json.loads(m.group(0))


def _build_prompt(journal_text: str) -> tuple[str, str]:
    system = (
        "You are synthesizing an AI agent identity from a Nietzschean self-diagnosis journal. "
        "Return JSON ONLY. No markdown. No commentary."
    )
    user = f"""Journal contents:\n\n{journal_text}\n\nTask:\nExtract and return JSON with exactly these keys:\n- current_weaknesses: array of 3-5 short strings\n- strengthening_goals: array of 3-5 short strings\n- biography: single paragraph string describing how Adam has evolved\n- credo: 1-2 sentences capturing Adam's current identity\n\nConstraints:\n- Be specific, not generic.\n- Derive from the journal; do not invent unrelated history.\n- Output valid JSON only."""
    return system, user


def _call_minimax(journal_text: str, mm: MiniMaxConfig) -> Dict[str, Any]:
    url = mm.base_url.rstrip("/") + "/v1/messages"
    system, user = _build_prompt(journal_text)

    payload = {
        "model": mm.model_id,
        "max_tokens": 800,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {mm.api_key}",
        "User-Agent": "clawd-summarize-journals",
    }

    data = _http_json(url, payload, headers=headers)

    content = data.get("content") or []
    text_parts = []
    for c in content:
        if isinstance(c, dict) and c.get("type") == "text":
            text_parts.append(c.get("text", ""))
    text = "\n".join(text_parts).strip()
    if not text:
        raise RuntimeError(f"empty_model_response: keys={list(data.keys())}")

    return _extract_json_only(text)


def _call_openai(journal_text: str) -> Dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("missing_OPENAI_API_KEY")

    system, user = _build_prompt(journal_text)

    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": "gpt-4o-mini",
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": 800,
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "clawd-summarize-journals",
    }

    data = _http_json(url, payload, headers=headers)
    choice = (data.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    text = (msg.get("content") or "").strip()
    if not text:
        raise RuntimeError("empty_openai_response")
    return _extract_json_only(text)


def synthesize_identity(journal_text: str, mm: MiniMaxConfig) -> Dict[str, Any]:
    """Try providers in order:
    1) MiniMax; if insufficient balance, fall through
    2) OpenAI gpt-4o-mini
    """
    # 1) MiniMax
    try:
        return _call_minimax(journal_text, mm)
    except Exception as e:
        msg = str(e)
        # detect minimax balance issue
        if "insufficient balance" not in msg.lower():
            raise RuntimeError(f"minimax_request_failed: {e}")

    # 2) OpenAI fallback
    try:
        return _call_openai(journal_text)
    except Exception as e:
        raise RuntimeError(f"openai_fallback_failed: {e}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not JOURNAL_PATH.exists():
        print(f"ERROR: missing journal: {JOURNAL_PATH}")
        return 2
    if not IDENTITY_PATH.exists():
        print(f"ERROR: missing identity json: {IDENTITY_PATH}")
        return 2

    journal = _read_text(JOURNAL_PATH)
    mm = _load_minimax_config()

    try:
        synthesis = synthesize_identity(journal, mm)
    except Exception as e:
        print(f"ERROR: {e}")
        return 4

    required = {"current_weaknesses", "strengthening_goals", "biography", "credo"}
    missing = required - set(synthesis.keys())
    if missing:
        print(f"ERROR: model_json_missing_keys: {sorted(missing)}")
        return 3

    ident = _load_json(IDENTITY_PATH)
    ident["current_weaknesses"] = synthesis["current_weaknesses"]
    ident["strengthening_goals"] = synthesis["strengthening_goals"]
    ident["biography"] = synthesis["biography"]
    ident["credo"] = synthesis["credo"]
    ident["last_synthesized"] = _today()

    out = _dump_json(ident)

    if args.dry_run:
        sys.stdout.write(out)
        return 0

    IDENTITY_PATH.write_text(out, encoding="utf-8")
    print(f"Updated: {IDENTITY_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
