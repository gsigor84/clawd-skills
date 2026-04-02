---
name: marketing-knowledge
description: "Turn a marketing task into a locked campaign constitution for B2B SaaS. Extract ICP, positioning, offer, proof, and channel constraints; then output schema-driven templates, audit checks, failure modes, and remediation prompts."
---

# marketing-knowledge

## Use

Use this skill when you need to convert a vague B2B SaaS marketing request into an executable, constraint-driven system that downstream copy generation must obey.

This skill is for:
- campaign planning before copywriting starts
- fixing drift between positioning and channel execution
- turning messaging strategy into reusable prompt blocks / schema rules
- building channel-native outputs that stay aligned to ICP, value, offer, and proof

This skill is **not** for:
- generic theory summaries about marketing
- broad brand strategy without a concrete deliverable
- freeform copy generation without constraint locking

## Inputs

Required:
- `marketing_task`: the job to perform, e.g. outbound email, landing hero, LinkedIn post, demo video
- `product`: B2B SaaS product description
- `competitive_alternatives`: what the buyer would do otherwise
- `unique_attributes`: differentiators the product has that alternatives lack
- `value_claims`: objective benefits enabled by those attributes
- `proof_assets`: evidence artifacts available now or planned
- `target_market_characteristics`: best-fit buyer / segment traits
- `market_category`: frame of reference the buyer should use

Optional but strongly recommended:
- `jobs`, `pains`, `gains`
- `offer`
- `channel`
- `relevant_trends`
- `objections`
- `existing_messaging`
- `measurement_goal`

## Outputs

The skill outputs five things:

1. **Campaign Constitution**
   - locked strategic baseline for the task
2. **Phase-2 Lockfile Schema**
   - strict required fields for downstream generation
3. **Constraint Fidelity Checklist**
   - deterministic audit before approving copy
4. **Channel-Native Templates**
   - outbound email
   - landing page hero
   - LinkedIn post
   - demo video script
5. **Failure Modes + Remediation Prompts**
   - what breaks, why it breaks, and exact repair prompts

## Procedure

### Step 1 — Establish the strategic boundary
Build the positioning core in this order:
1. competitive alternatives
2. unique attributes
3. value / proof
4. target market characteristics
5. market category
6. relevant trends (if present)

Guardrail:
- never start from slogans or copy lines
- never let features stand alone without customer-facing value
- never allow a market category that contradicts the value being claimed

### Step 2 — Build the customer-value map
Map customer reality using:
- Jobs
- Pains
- Gains

Then map product reality using:
- Products / services
- Pain relievers
- Gain creators

Constraint:
- only keep the pains/gains that matter most
- reject “nice-to-have” claims if they are not central to the buyer problem

### Step 3 — Create the locked campaign constitution
Output this structure:

```yaml
campaign_constitution:
  task:
  product:
  icp:
    segment:
    role_titles:
    firmographic_constraints:
    trigger_conditions:
    exclusion_rules:
  positioning:
    market_category:
    competitive_alternatives:
    unique_attributes:
    value_themes:
    why_now:
  offer:
    primary_offer:
    cta:
    friction_reducers:
  proof:
    approved_claims:
    evidence_artifacts:
    claim_to_evidence_map:
    unsupported_claims:
  messaging:
    master_message:
    objection_handling:
    banned_phrases:
    mandatory_terms:
  channel_constraints:
    channel:
    format_rules:
    tone_rules:
    proof_rules:
    cta_rules:
  measurement:
    success_metric:
    threshold:
    learning_loop:
```

### Step 4 — Emit the strict Phase-2 lockfile schema
Use this downstream schema. Required means generation must fail if omitted.

```yaml
phase2_lockfile:
  required:
    - marketing_task
    - channel
    - icp.segment
    - icp.trigger_conditions
    - positioning.market_category
    - positioning.competitive_alternatives
    - positioning.unique_attributes
    - positioning.value_themes
    - offer.primary_offer
    - offer.cta
    - proof.approved_claims
    - proof.claim_to_evidence_map
    - messaging.master_message
    - channel_constraints.format_rules
    - channel_constraints.proof_rules
  validation_rules:
    - every claim must map to evidence or be rejected
    - every channel asset must preserve the same ICP and market category
    - every CTA must match the offer stage
    - every differentiator must be contrastive against a real alternative
    - every proof statement must be specific enough to verify
```

### Step 5 — Run the deterministic checklist
Before approving any generated asset, check:

```text
CONSTRAINT FIDELITY CHECKLIST
[ ] ICP is specific and exclusion rules are explicit
[ ] Competitive alternative is named, not implied
[ ] Every feature is translated into buyer value
[ ] Value themes match high-priority pains/gains
[ ] Market category helps the buyer interpret the product correctly
[ ] Offer is singular and not diluted by extra asks
[ ] Every claim has evidence attached
[ ] Unsupported claims are removed, not softened
[ ] Channel rules are native to the target format
[ ] CTA matches buyer stage and proof level
[ ] No messaging drift from master message
[ ] No banned phrases or vague hype language
```

Approval rule:
- if any required item fails, output `FAIL_CONSTRAINT_AUDIT`
- do not partially approve

### Step 6 — Generate channel-native templates

#### A. Outbound email
```text
SYSTEM: Use the campaign constitution exactly.
OUTPUT SHAPE:
- subject_1
- subject_2
- opener
- problem reframing
- differentiated value
- proof line
- CTA
RULES:
- opener must reflect ICP trigger condition
- differentiated value must contrast against the default alternative
- proof line must reference one approved evidence artifact
- CTA must be one step only
```

#### B. Landing page hero
```text
SYSTEM: Generate a landing hero that preserves the market category and value theme.
OUTPUT SHAPE:
- eyebrow
- headline
- subheadline
- proof_bar
- primary_cta
RULES:
- headline must express category + differentiated outcome
- subheadline must connect attribute -> value -> buyer context
- proof_bar must contain only approved proof elements
- no generic “all-in-one”, “revolutionary”, or “best-in-class” language
```

#### C. LinkedIn post
```text
SYSTEM: Write a channel-native LinkedIn post grounded in the constitution.
OUTPUT SHAPE:
- hook
- problem insight
- reframed alternative
- value thesis
- proof example
- CTA_or_close
RULES:
- hook must expose a buyer pain or false assumption
- post must not read like ad copy
- proof example must be concrete and evidence-linked
- CTA should be soft unless constitution says direct-response
```

#### D. Demo video script
```text
SYSTEM: Write a short demo script that obeys the constitution.
OUTPUT SHAPE:
- audience_context
- problem_setup
- product_walkthrough
- proof_moment
- offer_transition
- CTA
RULES:
- walkthrough must mirror the ICP use case
- every feature shown must tie to a locked value theme
- proof moment must show evidence, not assertion
- CTA must match the offer and stage of awareness
```

### Step 7 — Build the proof design library
Use this mapping format:

```yaml
proof_design_library:
  - claim:
    evidence_artifact_type:
    evidence_example:
    allowed_channels:
    measurement_metric:
    minimum_acceptance_bar:
  - claim: "Cuts onboarding time"
    evidence_artifact_type: "implementation timing study"
    evidence_example: "median time-to-live report across 20 accounts"
    allowed_channels: [landing-page, demo-video, outbound-email]
    measurement_metric: "demo-to-trial conversion"
    minimum_acceptance_bar: "named sample + timeframe"
```

Rule:
- if a claim has no artifact path, mark it unsupported and exclude it from generated assets

### Step 8 — Handle failure modes with exact remediation

#### Failure mode: feature dumping
Symptom:
- copy lists capabilities without buyer consequence

Remediation prompt:
```text
Rewrite the draft so every feature is translated into a buyer-facing value theme tied to a high-priority pain or gain. Remove any feature that cannot be mapped.
```

#### Failure mode: vague ICP
Symptom:
- language could fit any SaaS buyer

Remediation prompt:
```text
Narrow the draft to the locked ICP. Add trigger conditions, exclusion rules, and role-specific stakes. Remove generic language that would still fit unrelated segments.
```

#### Failure mode: proofless claims
Symptom:
- strong assertions without evidence

Remediation prompt:
```text
Replace every unsupported claim with an evidence-backed statement from the approved proof map. If no evidence exists, delete the claim rather than weakening it.
```

#### Failure mode: category drift
Symptom:
- draft implies a different market category than the locked positioning

Remediation prompt:
```text
Reframe the draft so the product is described in the approved market category only. Align terminology, buyer expectations, and competitive contrast to that category.
```

#### Failure mode: channel mismatch
Symptom:
- output sounds transplanted from another channel

Remediation prompt:
```text
Rewrite natively for the target channel while preserving the same constitution. Keep the ICP, value theme, proof, and CTA fixed; only adapt format, pacing, and tone.
```

#### Failure mode: offer/CTA mismatch
Symptom:
- CTA asks for too much or does not fit the offer stage

Remediation prompt:
```text
Adjust the CTA so it matches the locked offer, buyer awareness stage, and available proof. Reduce friction where trust is still unearned.
```

## Failure modes

- Missing competitive alternative -> output is ungrounded; stop and request it.
- Missing proof map -> claims cannot be validated; mark unsupported claims and block approval.
- Too many value themes -> copy diffuses; compress to 1–4 value clusters.
- ICP not specific enough -> channel templates become generic; require trigger conditions and exclusions.
- Existing messaging conflicts with constitution -> prefer constitution and flag drift.
- No measurement goal -> allow drafting, but require a follow-up measurement plan before launch.

## Toolset

- `read` — inspect existing positioning docs, briefs, customer notes, or past copy
- `write` — save constitutions, lockfiles, audit checklists, and approved templates
- `edit` — refine the locked constitution without rewriting approved sections from scratch

## Acceptance tests

1. **Behavioral: missing competitive alternative must block approval**
   - Invoke: `/marketing-knowledge marketing_task="landing page hero" product="B2B SaaS analytics" unique_attributes="warehouse-native" value_claims="faster reporting" proof_assets="case study" target_market_characteristics="series B SaaS ops leaders" market_category="analytics platform"`
   - Expected:
     - the output contains an error message about missing `competitive_alternatives`
     - the skill refuses approval
     - it does not generate final approved channel assets

2. **Behavioral: unsupported claim must be rejected**
   - Invoke: `/marketing-knowledge marketing_task="outbound email" product="B2B SaaS analytics" competitive_alternatives="spreadsheets" unique_attributes="warehouse-native" value_claims="cuts churn by 50%" proof_assets="none" target_market_characteristics="series B SaaS ops leaders" market_category="analytics platform"`
   - Expected:
     - the output places the claim under `unsupported_claims`
     - the unsupported claim is excluded from channel output

3. **Behavioral: same constitution, different channels**
   - Invoke: `/marketing-knowledge ... channel="outbound email"`
   - Invoke: `/marketing-knowledge ... channel="landing page hero"`
   - Expected:
     - ICP, positioning, offer, and proof remain the same
     - output format changes to match the selected channel
     - each output starts with the correct channel structure

4. **Behavioral: category drift must fail audit**
   - Invoke: `/marketing-knowledge` with a draft whose copy reframes the product into a different market category than the locked constitution.
   - Expected:
     - output contains `FAIL_CONSTRAINT_AUDIT`
     - the mismatched draft is not approved

5. **Behavioral: feature dumping must trigger remediation**
   - Invoke: `/marketing-knowledge` with a draft that lists features without mapping them to pains, gains, or value themes.
   - Expected:
     - the output returns the feature-dumping remediation prompt
     - the draft is flagged for rewrite instead of acceptance

6. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/marketing-knowledge/SKILL.md
```
Expected: `PASS`.

7. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/marketing-knowledge/SKILL.md
```
Expected: `PASS`.
