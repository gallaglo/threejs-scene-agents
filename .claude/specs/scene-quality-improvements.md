# Three.js Scene Quality Improvement Spec

## Overview

This spec describes improvements to the `threejs-scene-agents` pipeline to produce
richer, more visually distinctive Three.js r128 scenes. It synthesizes:

- Analysis of the current pipeline architecture (from `SPEC.md`)
- Principles from the Anthropic frontend-design skill
  (`https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md`)
- Observed failure modes of AI-generated Three.js scenes

The changes touch four areas: the `VisionAgent` scene description schema, a new
two-pass planning step in `CodeGenAgent`, the `ValidatorAgent` scoring rubric, and
the `RefinementAgent` feedback loop.

---

## 1. VisionAgent — expand the scene description schema

### Problem

The current schema captures only a single object with one geometry, one animation,
and a flat background. This produces "object in a void" scenes with no depth,
atmosphere, or secondary elements.

### Change

Replace the flat schema with a richer structure. Update `VISION_PROMPT` to instruct
the agent to output this JSON shape:

```json
{
  "hero_element": "the single most visually distinctive thing in the scene",
  "hero_animation": "one primary animation for the hero — drift | orbit | pulse | sway | rise",
  "atmosphere": {
    "time_of_day": "dawn | morning | midday | dusk | night",
    "sky": "gradient hex top to bottom, e.g. ['#1a2a4a', '#87ceeb']",
    "fog": { "enabled": true, "color": "#hex", "near": 60, "far": 200 },
    "light_temperature": "warm | neutral | cool | dramatic"
  },
  "depth_layers": [
    { "layer": "background", "elements": ["snow-capped mountains", "sky dome"] },
    { "layer": "midground", "elements": ["alpine lake", "pine tree ring"] },
    { "layer": "foreground", "elements": ["meadow ground plane"] }
  ],
  "secondary_elements": [
    {
      "name": "alpine lake",
      "geometry": "CircleGeometry",
      "color": "#2a6090",
      "animation": "shimmer opacity",
      "layer": "midground"
    }
  ],
  "secondary_animations": [
    "clouds drift slowly left",
    "birds bob vertically on sine wave",
    "balloon sways on z-axis"
  ],
  "camera": {
    "position": [0, 8, 28],
    "look_at": [0, 6, 0],
    "fov": 55
  },
  "palette": ["#hex1", "#hex2", "#hex3", "#hex4"],
  "scene_complexity": "minimal | medium | rich"
}
```

**Key additions over the old schema:**

- `hero_element` + `hero_animation`: forces a deliberate single signature moment
- `atmosphere`: sky treatment, fog, and light temperature replace the flat `background` string
- `depth_layers`: requires the agent to think in foreground/midground/background
- `secondary_elements`: array instead of a single object — each with its own geometry, color, and animation
- `secondary_animations`: independent per-element animations, not one global animation
- `camera`: explicit positioning avoids the default z=5 close-up on a single object
- `scene_complexity`: a signal to CodeGenAgent about how much to build

---

## 2. CodeGenAgent — add a two-pass planning step

### Problem

CodeGenAgent goes directly from `scene_description` to code. This skips a creative
planning phase, producing generic output that defaults to the same Three.js patterns
regardless of the subject.

### Change

Update `CODEGEN_PROMPT` to require a two-pass approach before writing any code.

#### Pass 1 — scene brief (output as a comment block at the top of the generated code)

Before writing a single line of Three.js, the agent must define:

```
// SCENE BRIEF
// Hero moment: [the one visually memorable element and why]
// Depth layers: [background → midground → foreground elements]
// Signature animation: [the one primary animation; everything else is subtle]
// Anti-defaults check:
//   - NOT a single object in an empty void
//   - NOT everything rotating on all axes simultaneously
//   - NOT uniform grey/black fog with no sky treatment
//   - NOT only ambient + directional light with no color temperature
// Palette: [named hex values, 4–6 colors]
// Atmosphere: [sky, fog, light color rationale]
```

#### Pass 2 — code

Only after writing the brief comment block does the agent write the Three.js code,
deriving every color, light, and animation decision from the brief.

#### Mandatory scene requirements

Add these hard requirements to `CODEGEN_PROMPT`:

- At least **3 depth layers** (background, midground, foreground)
- At least **2 independently animated elements** (not just the hero)
- An **atmospheric treatment**: fog, sky gradient or sphere, or light color temperature
- A **ground plane or water plane** — scenes must have a surface
- **No single object floating in a void** — every scene needs an environment
- Secondary elements must have **their own subtle animations** (cloud drift, water shimmer, bird bob)
- Use **Lambert or Phong materials** for most scene elements; reserve Standard for hero highlights only (performance)
- **Spend boldness in one place**: the hero animation should be the most elaborate; everything else is quiet and supportive

#### Three.js AI default patterns to actively avoid

These are the Three.js equivalents of the generic AI design defaults — flag these
in the prompt as things the agent must not produce:

1. A single `SphereGeometry` or `BoxGeometry` on a black background with `rotation.x += 0.01`
2. `AmbientLight` + `DirectionalLight` only, both pure white, no color temperature
3. A flat `PlaneGeometry` ground with a `GridHelper` as the only visual texture
4. `OrbitControls` as a substitute for any designed camera behavior
5. All objects added at `position (0, 0, 0)` with no spatial composition

---

## 3. ValidatorAgent — replace holistic score with weighted rubric

### Problem

A single 0–100 holistic score gives the RefinementAgent no actionable direction.
Gemini Flash will score "basically working" code around 70–75 regardless of visual
quality, and refinement has no specific target.

### Change

Update `VALIDATOR_PROMPT` and `tools.py` to use a **weighted sub-score rubric**.

#### Rubric (total: 100 points)

| Dimension | Points | What to check |
|-----------|--------|---------------|
| **Correctness** | 40 | Runs without errors; targets r128 exactly; no `import`/`export`; valid `init(canvas)` wrapper returning `dispose()` |
| **Visual richness** | 30 | Has 3+ depth layers; secondary elements present; atmospheric treatment (fog, sky, light temp); not a void scene |
| **Animation quality** | 20 | Hero animation is intentional and smooth; at least 2 independently animated elements; no "everything rotates" |
| **Code hygiene** | 10 | No console errors; `dispose()` cleans up renderer and listeners; no memory leaks in animation loop |

#### Tool change

Update `set_validation_result` to accept structured feedback:

```python
def set_validation_result(
    score: int,
    correctness_score: int,
    richness_score: int,
    animation_score: int,
    hygiene_score: int,
    richness_feedback: str,   # specific missing elements
    animation_feedback: str,  # specific animation issues
    refinement_targets: list[str],  # ordered list of fixes for RefinementAgent
    tool_context: ToolContext
)
```

The `refinement_targets` list is the key addition — it passes specific, ordered
action items to the RefinementAgent rather than a freeform string.

Example `refinement_targets`:
```json
[
  "Add fog to the scene (scene.fog = new THREE.Fog(...))",
  "Animate clouds independently with a separate drift variable",
  "Replace black background with a sky sphere using vertex colors",
  "Add a ground plane — scene currently has no surface"
]
```

Exit condition remains: escalate when `score >= 80` or `iteration >= 3`.

---

## 4. RefinementAgent — iterate on targets, not vibes

### Problem

The RefinementAgent receives a freeform `validation_feedback` string and rewrites
the whole scene. This is imprecise — it may fix one thing and break another, and
has no sense of priority.

### Change

Update `REFINEMENT_PROMPT` to:

1. Read `refinement_targets` (the ordered list from the updated validator tool)
2. Address targets **in order**, fixing the highest-priority item first
3. Preserve everything that already works — surgical edits, not full rewrites
4. Re-check the scene brief comment block at the top of the code and ensure the
   rewrite stays true to the original creative direction

Add `refinement_targets` to the session state key table:

| Key | Type | Set by | Read by |
|-----|------|--------|---------|
| `refinement_targets` | `list[str]` | ValidatorAgent (via tool) | RefinementAgent |

---

## 5. Optional: add a StyleAgent between Vision and CodeGen

If scene quality is still inconsistent after the above changes, consider inserting
a dedicated `StyleAgent` between `VisionAgent` and `CodeGenAgent`.

**Role:** takes the raw `scene_description` JSON and expands it into a full creative
brief — analogous to a director's note or a design brief — before any code is written.

**Output key:** `scene_brief` (string, free prose + structured tokens)

**What it produces:**
- Named palette with rationale (e.g. "dawn golds #f5c842 for the balloon envelope,
  glacier blue #2a6090 for the lake, muted sage #4a7a45 for the meadow")
- One-sentence "hero moment" statement
- Depth layer plan with spatial reasoning
- Animation hierarchy (primary hero animation vs. quiet secondary movements)
- Anti-default confirmation: "This scene avoids X, Y, Z defaults because..."

This separates "what is in the scene" (VisionAgent) from "how should it feel and
be composed" (StyleAgent) from "write the code" (CodeGenAgent) — a cleaner
separation of concerns that maps directly to how the frontend-design skill's
two-pass planning process works.

**Pipeline with StyleAgent:**
```
VisionAgent → StyleAgent → CodeGenAgent → LoopAgent(ValidatorAgent, RefinementAgent)
```

---

## 6. frontend-design skill integration

Add the Anthropic frontend-design skill to the `.claude/skills/` directory:

```
.claude/skills/frontend-design/SKILL.md
```

Source: `https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md`

Reference it in `CODEGEN_PROMPT` and `VALIDATOR_PROMPT` as context. The most
directly applicable principles for Three.js generation:

- **"Spend boldness in one place"** → one hero animation, everything else quiet
- **"The hero is a thesis"** → open the scene with its most characteristic element
- **"Leverage motion deliberately"** → orchestrated moments over scattered effects;
  too much animation makes a scene feel AI-generated
- **"Ground it in the subject"** → derive palette, lighting, and atmosphere from the
  scene's actual world (alpine = cool morning light, mist, earth tones)
- **"Match complexity to the vision"** → a `scene_complexity: minimal` scene needs
  precision; a `rich` scene needs elaborate execution — don't default to medium for everything
- **Two-pass planning** → brainstorm before building; critique the plan against the
  brief before writing code

---

## Summary of changes

| File | Change |
|------|--------|
| `sub_agents/vision/prompt.py` | Replace flat schema with expanded JSON structure |
| `sub_agents/codegen/prompt.py` | Add two-pass brief + mandatory scene requirements + anti-default list |
| `sub_agents/validator/tools.py` | Add structured sub-scores and `refinement_targets` list to tool signature |
| `sub_agents/validator/prompt.py` | Replace holistic scoring with weighted rubric |
| `sub_agents/refinement/prompt.py` | Consume `refinement_targets` in order; surgical edits not full rewrites |
| `agent.py` | (Optional) add `StyleAgent` between `vision_agent` and `codegen_agent` |
| `.claude/skills/frontend-design/SKILL.md` | Add skill file (copy from anthropics/skills) |
| `SPEC.md` | Update session state key table to include `refinement_targets` (and `scene_brief` if StyleAgent added) |
