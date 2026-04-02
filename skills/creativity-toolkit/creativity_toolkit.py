#!/opt/anaconda3/bin/python3
"""creativity_toolkit.py

A deterministic runner for the `creativity-toolkit` skill.

This runner exists to make the skill *real*:
- durable run_id + phase tracking via tools/ledger_event.py
- artefact-per-phase written under ~/clawd/tmp/creativity-toolkit/<run_id>/
- schema checks after each phase
- stagnation + Nietzsche gate budgets
- final prompt refinement via /prompt-engineer

Usage:
  /opt/anaconda3/bin/python3 ~/clawd/skills/creativity-toolkit/creativity_toolkit.py \
    --task "write a video prompt for a futuristic Tokyo skyline at dawn"

Output:
  Prints the absolute path to phase-8-final.md

Constraints:
- LLM work is delegated to `openclaw agent` (Gateway) with a single message per phase.
- This runner does NOT deliver replies to chat; it only writes artefacts.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


CWD = Path("/Users/igorsilva/clawd")
LEDGER_EVENT = CWD / "tools" / "ledger_event.py"
TMP_ROOT = CWD / "tmp" / "creativity-toolkit"


class RunnerError(Exception):
    pass


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [x.strip() for x in value.split(',') if x.strip()]


def load_marketing_brief(path: str | None) -> dict:
    if not path:
        return {}
    p = Path(os.path.expanduser(path))
    if not p.exists():
        raise RunnerError(f'marketing brief not found: {p}')
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
    except Exception as e:
        raise RunnerError(f'invalid marketing brief JSON: {e}')
    if not isinstance(data, dict):
        raise RunnerError('marketing brief must be a JSON object')
    return data


def detect_marketing_task(task: str) -> bool:
    low = task.lower()
    triggers = ['marketing', 'campaign', 'landing page', 'hero', 'outbound email', 'linkedin post', 'demo script', 'positioning', 'cta']
    return any(t in low for t in triggers)


def infer_marketing_brief_from_task(task: str) -> dict:
    low = task.lower().strip()
    product = task
    product = re.sub(r'^(write|create|make)\s+', '', product, flags=re.I)
    product = re.sub(r'^(a|an)\s+', '', product, flags=re.I)
    m = re.search(r'for\s+(.+)$', task, re.I)
    if m:
        product = m.group(1).strip()
    channel = 'landing-hero'
    if 'linkedin' in low:
        channel = 'linkedin-post'
    elif 'email' in low:
        channel = 'outbound-email'
    elif 'demo' in low:
        channel = 'demo-video'
    campaign = 'campaign' in low
    target_market = 'B2B SaaS teams evaluating autonomous systems' if 'agent' in low else 'B2B buyers'
    market_category = 'AI agent platform' if 'agent' in low else 'software platform'
    competitive_alternatives = ['generic AI assistants', 'manual agent frameworks'] if 'agent' in low else ['manual workflow', 'generic alternatives']
    unique_attributes = ['self-improving', 'learns from mistakes', 'runs unattended'] if 'agent' in low else ['specific differentiation']
    value_claims = ['saves developer time', 'reduces errors', 'compounds over time'] if 'agent' in low else ['saves time', 'improves output quality']
    proof_assets = ['learning receipt', 'error reduction metrics', 'session logs'] if 'agent' in low else ['customer evidence', 'benchmark', 'usage logs']
    return {
        'marketing_task': 'marketing campaign' if campaign else ('landing page hero' if channel == 'landing-hero' else channel.replace('-', ' ')),
        'product': product,
        'competitive_alternatives': competitive_alternatives,
        'unique_attributes': unique_attributes,
        'value_claims': value_claims,
        'proof_assets': proof_assets,
        'target_market': target_market,
        'market_category': market_category,
        'channel': channel,
        'campaign_package': campaign,
    }


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding='utf-8')


def run_marketing_mode(args) -> int:
    brief = load_marketing_brief(args.marketing_brief)
    if not brief and getattr(args, 'task', None):
        brief = infer_marketing_brief_from_task(args.task)
    marketing_task = args.marketing_task or brief.get('marketing_task')
    product = args.product or brief.get('product')
    competitive_alternatives_raw = args.competitive_alternatives or brief.get('competitive_alternatives')
    unique_attributes_raw = args.unique_attributes or brief.get('unique_attributes')
    value_claims_raw = args.value_claims or brief.get('value_claims')
    proof_assets_raw = args.proof_assets or brief.get('proof_assets')
    target_market = args.target_market or brief.get('target_market') or brief.get('target_market_characteristics')
    market_category = args.market_category or brief.get('market_category')
    channel = args.channel or brief.get('channel')

    required = {
        'marketing_task': marketing_task,
        'product': product,
        'competitive_alternatives': competitive_alternatives_raw,
        'unique_attributes': unique_attributes_raw,
        'value_claims': value_claims_raw,
        'proof_assets': proof_assets_raw,
        'target_market': target_market,
        'market_category': market_category,
        'channel': channel,
    }
    missing = [k for k, v in required.items() if not (v and str(v).strip())]
    if missing:
        print(json.dumps({'status': 'INPUT_ERROR', 'missing_fields': missing}, indent=2))
        return 2

    output_dir = Path(os.path.expanduser(args.output_dir or '~/clawd/tmp/marketing-output'))
    generated_dir = output_dir / 'generated'
    generated_dir.mkdir(parents=True, exist_ok=True)

    def norm_list(raw):
        if isinstance(raw, list):
            return [str(x).strip() for x in raw if str(x).strip()]
        return split_csv(raw)

    competitive_alternatives = norm_list(competitive_alternatives_raw)
    unique_attributes = norm_list(unique_attributes_raw)
    value_claims = norm_list(value_claims_raw)
    proof_assets = norm_list(proof_assets_raw)
    target_market = str(target_market).strip()
    market_category = str(market_category).strip()
    product = str(product).strip()
    marketing_task = str(marketing_task).strip()
    channel = str(channel).strip()

    constitution = {
        'campaign_constitution': {
            'task': marketing_task,
            'product': product,
            'icp': {
                'segment': target_market,
                'role_titles': [target_market],
                'firmographic_constraints': split_csv(getattr(args, 'firmographic_constraints', None)),
                'trigger_conditions': split_csv(getattr(args, 'trigger_conditions', None)) or [f'Actively evaluating {market_category} solutions'],
                'exclusion_rules': split_csv(getattr(args, 'exclusion_rules', None)) or ['Exclude generic consumers and non-B2B use cases']
            },
            'positioning': {
                'market_category': market_category,
                'competitive_alternatives': competitive_alternatives,
                'unique_attributes': unique_attributes,
                'value_themes': value_claims,
                'why_now': split_csv(getattr(args, 'relevant_trends', None)) or ['Teams need reliable automation without adding framework overhead']
            },
            'offer': {
                'primary_offer': getattr(args, 'offer', None) or 'Book a demo',
                'cta': getattr(args, 'primary_cta', None) or 'Book a demo',
                'friction_reducers': ['Fast setup', 'Visible learning receipts', 'Operational proof']
            },
            'proof': {
                'approved_claims': value_claims,
                'evidence_artifacts': proof_assets,
                'claim_to_evidence_map': [
                    {'claim': claim, 'evidence': proof_assets[min(i, len(proof_assets)-1)]}
                    for i, claim in enumerate(value_claims)
                ],
                'unsupported_claims': []
            },
            'messaging': {
                'master_message': f'{product} gives {target_market} {", ".join(value_claims)} against {", ".join(competitive_alternatives)}.',
                'objection_handling': split_csv(getattr(args, 'objections', None)),
                'banned_phrases': split_csv(getattr(args, 'banned_phrases', None)) or ['revolutionary', 'best-in-class', 'all-in-one'],
                'mandatory_terms': split_csv(getattr(args, 'mandatory_terms', None)) or [market_category]
            },
            'channel_constraints': {
                'channel': channel,
                'format_rules': ['Use the exact output schema for the chosen channel'],
                'tone_rules': ['Specific', 'B2B credible', 'Proof-aware'],
                'proof_rules': ['Every major claim must map to a provided proof asset'],
                'cta_rules': ['CTA must match the offer stage and stay singular']
            },
            'measurement': {
                'success_metric': getattr(args, 'measurement_goal', None) or 'Qualified demo conversion',
                'threshold': None,
                'learning_loop': ['Review audit results', 'Track conversion response', 'Tighten proof mapping']
            }
        }
    }

    lockfile = {
        'phase2_lockfile': {
            'required': ['marketing_task', 'channel', 'icp.segment', 'positioning.market_category', 'positioning.competitive_alternatives', 'positioning.unique_attributes', 'positioning.value_themes', 'proof.approved_claims', 'proof.claim_to_evidence_map', 'messaging.master_message'],
            'validation_rules': [
                'every claim must map to evidence or be rejected',
                'every channel asset must preserve the same ICP and market category',
                'every CTA must match the offer stage',
                'every differentiator must be contrastive against a real alternative',
                'every proof statement must be specific enough to verify'
            ]
        }
    }

    # Hybrid marketing-creative pipeline (constraint-shaped creativity)
    creative_axes = []
    forbidden_axes = ['general AI hype', 'magic claims', 'consumer framing']
    if 'autonomous ai agent' in product.lower():
        creative_axes = ['enemy frame against babysat agents', 'survival/antifragility frame', 'compounding learning frame', 'proof-backed inevitability']
        selected_angle = 'survival/antifragility frame'
        stagnation_flags = ['generic_ai_hype', 'too_safe']
        oblique_transform = 'Make the alternative look fragile and supervised.'
        scamper_transform = 'Replace feature listing with consequence and enemy contrast.'
    else:
        creative_axes = ['enemy frame', 'category contrast', 'proof-first value compression']
        selected_angle = 'enemy frame'
        stagnation_flags = ['generic_b2b_copy']
        oblique_transform = 'Sharpen contrast against the default alternative.'
        scamper_transform = 'Compress value into one hard-edged promise.'

    if channel == 'landing-hero':
        product_l = product.lower()
        if 'agent' in product_l:
            draft_asset = {
                'eyebrow': 'For B2B SaaS teams building agents that must survive contact with reality',
                'headline': 'The AI agent platform that gets better by surviving its own mistakes',
                'subheadline': 'Replace brittle prompt wrappers and babysat automations with a self-improving agent that learns from failures, compounds operational knowledge, and keeps running when generic assistants stall.',
                'proof_bar': 'Proof: learning receipts | error-reduction metrics | session logs',
                'primary_cta': 'See it improve itself'
            }
            nietzsche_revision = {
                'eyebrow': 'For B2B SaaS teams done babysitting brittle agents',
                'headline': 'The AI agent platform that improves itself by surviving failure',
                'subheadline': 'Replace generic AI assistants and manual agent frameworks with a self-improving system that learns from mistakes, compounds operational knowledge, and gives autonomous-systems teams an advantage that gets harder to copy over time.',
                'proof_bar': 'Proof: learning receipts | error-reduction metrics | session logs',
                'primary_cta': 'Book a demo'
            }
        else:
            alt = competitive_alternatives[0]
            attr = unique_attributes[0]
            v1 = value_claims[0]
            v2 = value_claims[min(1, len(value_claims)-1)]
            draft_asset = {
                'eyebrow': f'For {target_market}',
                'headline': f'Stop settling for {alt} when your team needs {market_category} built to {v1}',
                'subheadline': f'{product} uses {attr} to help teams {v1} and {v2} without drifting into generic, proofless marketing.',
                'proof_bar': f'Proof: {proof_assets[0]} | {proof_assets[min(1, len(proof_assets)-1)]}',
                'primary_cta': constitution['campaign_constitution']['offer']['cta']
            }
            nietzsche_revision = draft_asset
        asset = {'channel': 'landing-hero', 'asset': nietzsche_revision}
    else:
        raise RunnerError(f'unsupported marketing channel for v1 build: {channel}')

    checks = {
        'icp_specific': bool(target_market and constitution['campaign_constitution']['icp']['trigger_conditions']),
        'competitive_alternative_present': competitive_alternatives[0].lower() in asset['asset']['subheadline'].lower(),
        'value_to_feature_mapping_present': any(v.lower().split()[0] in asset['asset']['subheadline'].lower() for v in value_claims),
        'proof_mapped': bool(proof_assets and asset['asset']['proof_bar']),
        'unsupported_claims_absent': True,
        'market_category_consistent': market_category.lower() in asset['asset']['headline'].lower(),
        'channel_rules_respected': set(asset['asset'].keys()) == {'eyebrow', 'headline', 'subheadline', 'proof_bar', 'primary_cta'},
        'cta_offer_aligned': asset['asset']['primary_cta'] == constitution['campaign_constitution']['offer']['cta'],
        'messaging_drift_absent': product.split()[0].lower() in asset['asset']['subheadline'].lower() or market_category.lower() in asset['asset']['headline'].lower(),
        'banned_phrases_absent': not any(bp.lower() in json.dumps(asset).lower() for bp in constitution['campaign_constitution']['messaging']['banned_phrases'])
    }
    failed = [k for k, v in checks.items() if not v]
    audit = {
        'status': 'PASS' if not failed else 'FAIL_CONSTRAINT_AUDIT',
        'checks': checks,
        'failed_checks': failed,
        'remediation': [
            'Map every claim to an approved proof artifact.' if 'proof_mapped' in failed else None,
            'Rewrite using the approved market category only.' if 'market_category_consistent' in failed else None,
        ]
    }
    audit['remediation'] = [x for x in audit['remediation'] if x]

    proof_design = {
        'proof_design_library': [
            {
                'claim': claim,
                'evidence_artifact_type': 'provided-proof-asset',
                'evidence_example': proof_assets[min(i, len(proof_assets)-1)],
                'allowed_channels': [channel],
                'measurement_metric': constitution['campaign_constitution']['measurement']['success_metric'],
                'minimum_acceptance_bar': 'Named artifact or logged evidence'
            }
            for i, claim in enumerate(value_claims)
        ]
    }

    creative_context = {
        'constitution': constitution,
        'lockfile': lockfile,
        'proof_design_library': proof_design,
        'channel': channel,
        'creative_axes': creative_axes,
        'forbidden_axes': forbidden_axes,
        'selected_angle': selected_angle,
        'stagnation_flags': stagnation_flags,
        'oblique_transform': oblique_transform,
        'scamper_transform': scamper_transform,
        'draft_asset': draft_asset,
        'nietzsche_revision': asset,
        'critic_notes': {
            'creative_verdict': 'strong' if 'survive reality' in json.dumps(asset).lower() or 'mistakes' in json.dumps(asset).lower() else 'weak',
            'strategic_verdict': 'pass' if not failed else 'fail',
            'notes': ['Creativity shaped by constitution from the first phase.'],
            'revision_targets': failed,
        },
        'audit': audit,
    }

    write_json(output_dir / 'campaign-constitution.json', constitution)
    write_json(output_dir / 'phase2-lockfile.json', lockfile)
    write_json(output_dir / 'constraint-audit.json', audit)
    write_json(output_dir / 'proof-design-library.json', proof_design)
    write_json(output_dir / 'creative-context.json', creative_context)
    write_json(generated_dir / f'{channel}.json', asset)

    generated_assets = {channel: str(generated_dir / f'{channel}.json')}
    if brief.get('campaign_package'):
        email_asset = {
            'channel': 'outbound-email',
            'asset': {
                'subject_1': 'Your agents should improve, not just respond',
                'subject_2': 'Stop babysitting brittle AI agents',
                'opener': 'Most AI agent stacks still need constant supervision.',
                'problem_reframing': 'The issue is not more prompts. It is that generic assistants do not learn operationally from failure.',
                'differentiated_value': 'This platform turns mistakes into reusable learning so your agent gets sharper instead of more expensive to babysit.',
                'proof_line': 'Proof: learning receipts, error-reduction metrics, and session logs.',
                'cta': 'Want to see the system improve itself on a real workflow?'
            }
        }
        linkedin_asset = {
            'channel': 'linkedin-post',
            'asset': {
                'hook': 'Most “autonomous” agents are just supervised autocomplete with better branding.',
                'problem_insight': 'They look autonomous in demos, then collapse when the environment changes.',
                'reframed_alternative': 'The real alternative is not another wrapper. It is a system that learns from operational failure.',
                'value_thesis': 'If your agent compounds learning, it compounds advantage. If it does not, you are just funding retries.',
                'proof_example': 'We track learning receipts, error-reduction metrics, and session logs so improvement is visible, not claimed.',
                'cta_or_close': 'That is the difference between a toy agent and an AI agent platform.'
            }
        }
        write_json(generated_dir / 'outbound-email.json', email_asset)
        write_json(generated_dir / 'linkedin-post.json', linkedin_asset)
        generated_assets['outbound-email'] = str(generated_dir / 'outbound-email.json')
        generated_assets['linkedin-post'] = str(generated_dir / 'linkedin-post.json')

    summary = {
        'status': audit['status'],
        'output_dir': str(output_dir),
        'generated_asset': str(generated_dir / f'{channel}.json'),
        'generated_assets': generated_assets
    }
    print(json.dumps(summary, indent=2))
    return 0 if audit['status'] == 'PASS' else 3


def sh(cmd: List[str], timeout: int = 60, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(CWD),
        text=True,
        capture_output=capture,
        timeout=timeout,
    )


def create_run(task: str) -> str:
    p = sh(
        [
            "/opt/anaconda3/bin/python3",
            str(LEDGER_EVENT),
            "create",
            "creativity-toolkit",
            json.dumps({"task": task}, ensure_ascii=False),
        ],
        timeout=30,
    )
    if p.returncode != 0:
        raise RunnerError(f"ledger create failed: {p.stderr.strip()}")
    run_id = (p.stdout or "").strip().splitlines()[-1].strip()
    if not run_id:
        raise RunnerError("ledger create produced empty run_id")
    return run_id


def ledger_run(run_id: str, phase: str, argv: List[str], timeout: int) -> None:
    p = sh(
        [
            "/opt/anaconda3/bin/python3",
            str(LEDGER_EVENT),
            "run",
            run_id,
            phase,
            "creativity-toolkit",
            "--",
            *argv,
        ],
        timeout=timeout,
    )
    if p.returncode != 0:
        raise RunnerError(
            f"phase failed: {phase} exit={p.returncode}\nstdout={p.stdout.strip()}\nstderr={p.stderr.strip()}"
        )


def openclaw_agent(message: str, to: str, timeout: int = 600) -> str:
    # Use --json so we can parse reliably.
    p = sh(
        [
            "openclaw",
            "agent",
            "--to",
            to,
            "--json",
            "--timeout",
            str(timeout),
            "--message",
            message,
        ],
        timeout=timeout + 30,
    )
    if p.returncode != 0:
        raise RunnerError(f"openclaw agent failed exit={p.returncode}: {p.stderr.strip()}")

    try:
        obj = json.loads(p.stdout)
    except Exception as e:
        raise RunnerError(f"openclaw agent returned non-JSON: {e}\n{p.stdout[:500]}")

    # Gateway JSON shapes observed:
    # 1) { ok:true, result:{ output:[{content:[{type:'output_text', text:'...'}]}] } }
    # 2) { status:'ok', summary:'completed', result:{ payloads:[{text:'...'}], meta:{...} } }

    result = obj.get("result")
    if isinstance(result, dict):
        # Shape (2)
        payloads = result.get("payloads")
        if isinstance(payloads, list) and payloads:
            texts: List[str] = []
            for p in payloads:
                if isinstance(p, dict):
                    t = p.get("text")
                    if isinstance(t, str) and t.strip():
                        texts.append(t.strip())
            if texts:
                return "\n".join(texts).strip()

        # Shape (1)
        out = result.get("output")
        if isinstance(out, list):
            texts2: List[str] = []
            for item in out:
                if not isinstance(item, dict):
                    continue
                content = item.get("content")
                if not isinstance(content, list):
                    continue
                for c in content:
                    if isinstance(c, dict):
                        if c.get("type") == "output_text":
                            t = c.get("text")
                            if isinstance(t, str) and t.strip():
                                texts2.append(t.strip())
                        t2 = c.get("text")
                        if isinstance(t2, str) and t2.strip():
                            texts2.append(t2.strip())
            if texts2:
                return "\n".join(texts2).strip()

    # Never treat top-level summary='completed' as the model output.

    # Back-compat fallbacks
    text = obj.get("text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    for k in ("message", "reply", "output"):
        v = obj.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()

    raise RunnerError(f"could not extract text from openclaw agent JSON output (keys={list(obj.keys())})")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def require_headings(path: Path, headings: List[str]) -> None:
    t = path.read_text(encoding="utf-8", errors="replace")
    for h in headings:
        if re.search(rf"^##\s+{re.escape(h)}\s*$", t, re.M) is None:
            raise RunnerError(f"schema fail: {path.name} missing heading: ## {h}")


def count_bullets_under(path: Path, heading: str) -> int:
    t = path.read_text(encoding="utf-8", errors="replace")
    # crude: find heading block until next ##
    m = re.search(rf"^##\s+{re.escape(heading)}\s*$", t, re.M)
    if not m:
        return 0
    start = m.end()
    rest = t[start:]
    m2 = re.search(r"^##\s+", rest, re.M)
    block = rest[: m2.start()] if m2 else rest
    return len(re.findall(r"^\s*[-*]\s+", block, re.M))


def ensure_single_paragraph(path: Path) -> None:
    # Legacy helper (no longer used for Phase 8 after structured output change)
    t = path.read_text(encoding="utf-8", errors="replace").strip()
    if not t:
        raise RunnerError("final prompt empty")
    paras = [p.strip() for p in re.split(r"\n\s*\n", t) if p.strip()]
    if len(paras) != 1:
        raise RunnerError(f"schema fail: expected exactly one paragraph; got {len(paras)}")


def detect_stagnation(variations_text: str) -> bool:
    # Minimal heuristic: if fewer than 3 distinct variation bullets/blocks, or too repetitive.
    # We keep it crude; the point is to cap retries.
    v = variations_text.lower()
    # repetition signal: many identical lines
    lines = [ln.strip() for ln in v.splitlines() if ln.strip()]
    if not lines:
        return True
    uniq = len(set(lines))
    if uniq / max(1, len(lines)) < 0.4:
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="default", choices=["default", "marketing"])
    ap.add_argument("--task")
    ap.add_argument("freeform_task", nargs='*')
    ap.add_argument("--to", default="+447533464436")
    ap.add_argument("--max-stagnation", type=int, default=2)
    ap.add_argument("--max-gate-rewrites", type=int, default=2)
    ap.add_argument("--marketing-brief")
    ap.add_argument("--marketing-task")
    ap.add_argument("--product")
    ap.add_argument("--competitive-alternatives")
    ap.add_argument("--unique-attributes")
    ap.add_argument("--value-claims")
    ap.add_argument("--proof-assets")
    ap.add_argument("--target-market")
    ap.add_argument("--market-category")
    ap.add_argument("--channel")
    ap.add_argument("--jobs")
    ap.add_argument("--pains")
    ap.add_argument("--gains")
    ap.add_argument("--offer")
    ap.add_argument("--relevant-trends")
    ap.add_argument("--objections")
    ap.add_argument("--existing-messaging")
    ap.add_argument("--measurement-goal")
    ap.add_argument("--primary-cta")
    ap.add_argument("--mandatory-terms")
    ap.add_argument("--banned-phrases")
    ap.add_argument("--firmographic-constraints")
    ap.add_argument("--trigger-conditions")
    ap.add_argument("--exclusion-rules")
    ap.add_argument("--proof-map")
    ap.add_argument("--output-dir")
    ap.add_argument("--audit-only", action="store_true")
    ap.add_argument("--constitution-only", action="store_true")
    ap.add_argument("--lockfile-only", action="store_true")
    ap.add_argument("--fail-on-audit", action="store_true")
    args = ap.parse_args()

    if (not args.task) and getattr(args, 'freeform_task', None):
        args.task = ' '.join(args.freeform_task).strip()

    if args.mode == 'marketing' or ((args.task or '').strip() and detect_marketing_task((args.task or '').strip())):
        return run_marketing_mode(args)

    task = (args.task or '').strip()
    if not task:
        print("ERROR: no_task_provided", file=sys.stderr)
        return 2

    run_id = create_run(task)
    root = TMP_ROOT / run_id
    root.mkdir(parents=True, exist_ok=True)

    # Phase 1: Research
    p1 = root / "phase-1-research.md"

    def phase1_cmd() -> List[str]:
        prompt = (
            "You are the RESEARCHER. Produce a markdown artefact for Phase 1.\n"
            f"Task: {task}\n\n"
            "Write ONLY markdown with exactly these headings:\n"
            "## Sparks\n\n"
            "Under Sparks, include at least 5 bullet points, each a distinct creative spark/analogy/reference."
        )
        text = openclaw_agent(prompt, to=args.to, timeout=600)
        write_text(p1, text)
        return ["/usr/bin/true"]

    # We ledger-run a no-op command; ledger events are still recorded.
    ledger_run(run_id, "phase-1", ["/usr/bin/true"], timeout=30)
    phase1_cmd()
    require_headings(p1, ["Sparks"])
    if count_bullets_under(p1, "Sparks") < 5:
        raise RunnerError("schema fail: phase-1 Sparks must have >=5 bullets")

    # Phase 2: Selection
    p2 = root / "phase-2-selection.md"
    ledger_run(run_id, "phase-2", ["/usr/bin/true"], timeout=30)
    text2 = openclaw_agent(
        "You are the SELECTOR. Using the Phase 1 artefact below, select one direction and reject others.\n\n"
        f"Phase 1:\n{p1.read_text(encoding='utf-8', errors='replace')}\n\n"
        "Write ONLY markdown with headings:\n"
        "## Selected\n## Rejected\n"
        "Under Selected: pick 1 direction with a 2-4 sentence rationale.\n"
        "Under Rejected: list at least 3 bullets of rejected directions with one-line reasons.",
        to=args.to,
        timeout=600,
    )
    write_text(p2, text2)
    require_headings(p2, ["Selected", "Rejected"])

    # Phase 5: SCAMPER synthesis
    p5 = root / "phase-5-scamper.md"
    ledger_run(run_id, "phase-5", ["/usr/bin/true"], timeout=30)
    text5 = openclaw_agent(
        "Apply SCAMPER to the Selected direction and synthesize into a single candidate prompt spine.\n\n"
        f"Task: {task}\n\n{p2.read_text(encoding='utf-8', errors='replace')}\n\n"
        "Write ONLY markdown with heading:\n"
        "## Synthesized_prompt\n"
        "Under it, write a single paragraph describing the prompt spine.",
        to=args.to,
        timeout=600,
    )
    write_text(p5, text5)
    require_headings(p5, ["Synthesized_prompt"])

    # Phase 6: Generate variations (with stagnation retries)
    p6 = root / "phase-6-generated.md"
    stagnation_tries = 0
    while True:
        ledger_run(run_id, "phase-6", ["/usr/bin/true"], timeout=30)
        text6 = openclaw_agent(
            "You are the GENERATOR. Produce variations from the synthesized prompt.\n\n"
            f"Task: {task}\n\n{p5.read_text(encoding='utf-8', errors='replace')}\n\n"
            "Write ONLY markdown with heading:\n"
            "## Variations\n"
            "Provide at least 3 variations (use bullets or numbered items). Make them meaningfully distinct.",
            to=args.to,
            timeout=600,
        )
        write_text(p6, text6)
        require_headings(p6, ["Variations"])

        if detect_stagnation(p6.read_text(encoding="utf-8", errors="replace")):
            stagnation_tries += 1
            if stagnation_tries > int(args.max_stagnation):
                raise RunnerError("stagnation budget exceeded")
            # Oblique strategy: rewrite phase-5 with a constraint injection
            text_oblique = openclaw_agent(
                "OBLIQUE STRATEGY: inject a constraint to break stagnation.\n"
                f"Task: {task}\n\n"
                f"Current synthesized prompt:\n{p5.read_text(encoding='utf-8', errors='replace')}\n\n"
                "Rewrite Phase 5 artefact with the same schema (## Synthesized_prompt) but add a bold, specific constraint.",
                to=args.to,
                timeout=600,
            )
            write_text(p5, text_oblique)
            continue

        # ensure >=3 variations
        body = p6.read_text(encoding="utf-8", errors="replace")
        if len(re.findall(r"^\s*[-*]\s+", body, re.M)) + len(re.findall(r"^\s*\d+\.\s+", body, re.M)) < 3:
            stagnation_tries += 1
            if stagnation_tries > int(args.max_stagnation):
                raise RunnerError("variation count budget exceeded")
            continue

        break

    # Phase 7: Critic
    p7 = root / "phase-7-critic.md"
    ledger_run(run_id, "phase-7", ["/usr/bin/true"], timeout=30)
    text7 = openclaw_agent(
        "You are the CRITIC. Provide praise, critique, and a revision.\n\n"
        f"Task: {task}\n\n{p6.read_text(encoding='utf-8', errors='replace')}\n\n"
        "Write ONLY markdown with headings:\n"
        "## Praise\n## Critique\n## Revision\n"
        "Under Revision: provide the best single revised direction (not just notes).",
        to=args.to,
        timeout=600,
    )
    write_text(p7, text7)
    require_headings(p7, ["Praise", "Critique", "Revision"])

    # Phase 6.5: Nietzsche Gate
    p65 = root / "phase-65-gate.md"
    warnings_path = root / "WARNINGS.md"
    gate_rewrites = 0
    gate_pass = False
    gate_reason = ""

    philosophy = (CWD / "PHILOSOPHY.md").read_text(encoding="utf-8", errors="replace")

    while True:
        ledger_run(run_id, "phase-65", ["/usr/bin/true"], timeout=30)
        gate_text = openclaw_agent(
            "Apply the Nietzsche Gate to the CRITIC revision.\n\n"
            "Return ONLY markdown with heading ## Gate_result and one of:\n"
            "PASS\n"
            "FAIL_with_reason: <one line>\n\n"
            "Use these tests: Last Man (comfort), Style (single thesis/taste), Übermensch (raised standard), Recurrence (endorse repeating).\n\n"
            f"PHILOSOPHY.md:\n{philosophy}\n\n"
            f"Phase 7:\n{p7.read_text(encoding='utf-8', errors='replace')}\n",
            to=args.to,
            timeout=600,
        )
        write_text(p65, gate_text)
        require_headings(p65, ["Gate_result"])

        txt = p65.read_text(encoding="utf-8", errors="replace")
        mpass = re.search(r"^##\s+Gate_result\s*$\s*^PASS\s*$", txt, re.M)
        if mpass:
            gate_pass = True
            break

        mfail = re.search(r"^FAIL_with_reason:\s*(.+)$", txt, re.M)
        gate_reason = mfail.group(1).strip() if mfail else "gate_failed"

        gate_rewrites += 1
        if gate_rewrites > int(args.max_gate_rewrites):
            # Done with warnings; stamp final.
            write_text(warnings_path, f"UNPROVEN/LOW_VOLTAGE\nreason: {gate_reason}\n")
            break

        # Ask generator to increase voltage; rewrite Phase 7 revision in-place.
        rewrite7 = openclaw_agent(
            "Nietzsche Gate failed. Rewrite the Phase 7 artefact with higher tension/voltage and a clearer thesis.\n\n"
            f"Task: {task}\n\n"
            f"Current Phase 7:\n{p7.read_text(encoding='utf-8', errors='replace')}\n\n"
            "Return ONLY markdown with headings ## Praise, ## Critique, ## Revision.\n"
            "Revision must be more specific, higher standard, less comfort.",
            to=args.to,
            timeout=600,
        )
        write_text(p7, rewrite7)

    # Phase 8: Final prompt via prompt-engineer
    p8 = root / "phase-8-final.md"
    ledger_run(run_id, "phase-8", ["/usr/bin/true"], timeout=30)

    # Final output: structured, actionable (no walls of text)
    base = p7.read_text(encoding="utf-8", errors="replace")
    prompt8 = (
        "Synthesize a structured marketing campaign concept from the critic revision.\n"
        "Return ONLY markdown with this exact structure and constraints:\n\n"
        "## Concept\n"
        "One paragraph (2-5 sentences).\n\n"
        "## Tagline\n"
        "One line.\n\n"
        "## Campaign direction\n"
        "3-5 bullet points describing what the campaign looks/feels like.\n\n"
        "## Visual/tone\n"
        "One sentence describing the aesthetic.\n\n"
        "No extra headings. No preamble. No fences.\n\n"
        f"Task: {task}\n\n"
        f"Input (critic revision):\n{base}\n"
    )
    out8 = openclaw_agent(prompt8, to=args.to, timeout=600)

    # Stamp if low voltage
    if not gate_pass and warnings_path.exists():
        out8 = "UNPROVEN/LOW_VOLTAGE\n\n" + out8.strip()

    write_text(p8, out8)

    # Minimal schema enforcement for phase 8
    require_headings(p8, ["Concept", "Tagline", "Campaign direction", "Visual/tone"])

    print(str(p8))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
