# clawd/skills

OpenClaw skills for Igor’s workspace (`~/clawd/skills/`). Each skill lives in its own folder and is defined by `SKILL.md`.

## Use a skill (one-liner)
Type its slash command in chat, e.g.:

- `/summarize https://example.com`

## Create a new skill
Use the single entry point:

- `/new-skill <what you want the skill to do>`

If the request overlaps an existing skill, the pipeline will stop and ask whether to proceed, improve an existing skill, or cancel.

## Improve existing skills
Run the deterministic patch loop:

- `/improve-skills`  
  (optionally: `/improve-skills --targets <skill-name> ...`)

## Organisation
- One skill per folder: `skills/<skill-name>/SKILL.md`
- Optional extras:
  - `skills/<skill-name>/scripts/` (deterministic helpers)
  - `skills/<skill-name>/references/` (large docs)

Index (coming soon): `SKILLS.md`
