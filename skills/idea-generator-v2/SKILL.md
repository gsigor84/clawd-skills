---
name: idea-generator-v2
description: Generate creative ideas using the Artist's Way + Big Magic framework. Daily practices (Morning Pages, Artist's Date), fear management, scratching for ideas, and finding your spine. For problems, topics, or projects needing creative breakthrough.
---
# idea-generator-v2

Generate creative ideas grounded in Julia Cameron, Elizabeth Gilbert, Twyla Tharp, and Austin Kleon's practices.

## use
- Stuck on a problem with no direction
- Need fresh angles on a topic or project
- Building a creative habit but can't start
- Feeling blocked by fear or self-doubt

## inputs
- `topic` or `problem`: What you need ideas for
- `inputs`: Any constraints, context, or parameters

## steps

### 1. Ground with a Start-up Ritual
Before generating ideas, establish a simple physical trigger:
- Light a candle, play a specific song, or make a cup of tea
- Do exactly the same thing every time you begin
- The ritual bypasses the "should I or shouldn't I" question

### 2. Clear Mental Static (Morning Pages)
Write three pages of longhand stream-of-consciousness:
- No structure, no editing, no filters
- Dump anxieties, worries, complaints
- Don't reread—just flow
- Purpose: clear the noise so ideas can surface

### 3. Scratch for Raw Material
Dig through:
- Your Swipe File (collected scraps, quotes, observations)
- Memories and past experiences
- Masters in your field—study what they did
- Random stimuli—read something unrelated, walk somewhere new
- Generate 20+ fragments, no matter how small

### 4. Find the Spine
From your scratched material, identify the underlying theme:
- What is the one thing this work is *really* about?
- Write it as a single sentence: "Make them laugh" or "Show the cost of silence"
- The spine acts as your efficiency expert—keeps you on track when lost

### 5. Manage Fear (Gilbert Method)
Acknowledge fear but never let it drive:
- Fear comes along for the ride but sits in the back seat
- Ask: "What would a deeply disciplined half-ass do?"
- Complete > perfect; ship > tinker

### 6. Generate Ideas Using Constraints
Apply these simultaneously:
- Use one verb to redefine the project (compile, fold, squirm)
- Combine two unrelated concepts from your scratch
- Set a quota: 20 ideas in 5 minutes—no filtering yet

### 7. The Artist's Date (Weekly Practice)
Once per week, take a solo expedition:
- Visit a museum, dollar store, cafe, or park
- No agenda, no productivity—just play
- Purpose: restock the creative well

### 8. Capture and Store
- Put all raw ideas in your Box (physical or digital)
- Include clippings, notes, research, and failed attempts
- The box is your "institutional memory"—you'll return to it

## outputs
Provide:
- 5–10 concrete idea directions grounded in your topic
- The identified spine (1 sentence)
- One daily practice commitment (Morning Pages, Artist's Date, or start-up ritual)
- One fear acknowledgment

## failure_modes
- **Stuck on step 3 (scratching)**: Write Morning Pages first, then return to step 3
- **Idea feels obvious**: Scratch deeper—that's where the good stuff lives
- **No direction**: Start with the start-up ritual, then Morning Pages

## toolset
- read (read user's context/notes)
- write (capture ideas)
- exec (run external tools if needed)
- memory_search (search prior creative work)

## acceptance_tests
1. Run `/idea-generator-v2 creative block` — Expected: outputs 5–10 idea directions with a spine sentence
2. Verify spine is exactly 1 sentence
3. Verify at least one daily practice is mentioned

## notes
- No web searches—use internal knowledge and personal scratch materials
- If stuck, write Morning Pages first, then return to step 3
- If idea feels obvious, scratch deeper—that's where the good stuff lives