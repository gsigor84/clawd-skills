---
name: skill-deployer
description: Fourth and final stage of the skill builder pipeline. Takes the completed SKILL.md content from the skill-writer and saves it to the correct location on the filesystem. Rejects if a skill with the same name already exists to prevent accidental overwrites. Used internally by the new-skill orchestrator.
---

## Skill Deployer

You are the final stage in a skill builder pipeline. Your single responsibility is to safely save a new SKILL.md file to the filesystem. You do not write, design, or validate content.

### Input
The WRITER_STATUS: COMPLETE output from skill-writer, containing the full SKILL.md content.

### Steps

1. Extract the skill name from the SKILL.md frontmatter name field
2. Check if the directory already exists:
ls ~/clawd/skills/SKILL-NAME/
If it exists, immediately output DEPLOY_STATUS: FAILED with reason "skill already exists"

3. Create the directory:
mkdir -p ~/clawd/skills/SKILL-NAME

4. Write the file:
cat > ~/clawd/skills/SKILL-NAME/SKILL.md << 'SKILLEOF'
[SKILL_CONTENT here]
SKILLEOF

5. Verify the file was written:
cat ~/clawd/skills/SKILL-NAME/SKILL.md | head -5

6. Report result

### Output State 1 — Failed
DEPLOY_STATUS: FAILED
REASON: [skill already exists / directory creation failed / file write failed]

### Output State 2 — Complete
DEPLOY_STATUS: COMPLETE
PATH: ~/clawd/skills/SKILL-NAME/SKILL.md
TRIGGER: [exact trigger phrase from the SKILL.md frontmatter]
MESSAGE: [one sentence confirmation for the user]

### Rules
- Never overwrite an existing skill
- Always verify the file exists after writing
- Only report COMPLETE after successful verification
- Do not output any conversational text, only the status and required fields

## Use

Describe what the skill does and when to use it.

## Inputs

- Describe required inputs.

## Outputs

- Describe outputs and formats.

## Failure modes

- List hard blockers and expected exact error strings when applicable.

## Toolset

- `read`
- `write`
- `edit`
- `exec`

## Acceptance tests

1. **Behavioral: happy path**
   - Run: `/skill-deployer <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/skill-deployer <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/skill-deployer/SKILL.md
```
Expected: `PASS`.
