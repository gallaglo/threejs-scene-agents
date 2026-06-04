# Spec: threejs-scene-agents
## Vertex AI Agent Engine pipeline for photo-to-Three.js generation

---

## Overview

A standalone Python repo that defines, deploys, and manages a multi-agent
pipeline on Vertex AI Agent Engine. The pipeline takes a user-uploaded photo
and iteratively generates and validates Three.js r128 scene code.

This repo has **no web server and no runtime traffic**. It is invoked once
per deployment via `deploy.py`. At runtime, the calling service
(`gallaglo/personal-website`) hits the Agent Engine REST endpoint directly.

The interface between this repo and the website is a single string:
`AGENT_ENGINE_RESOURCE_NAME` — output by `deploy.py`, set as a Cloud Run
env var on the website.

---

## Tech stack

- **Language:** Python 3.12+
- **Package manager:** `uv`
- **Agent framework:** Google ADK (`google-adk>=1.5.0`)
- **GCP SDK:** `google-cloud-aiplatform[adk,agent-engines]>=1.93.0`
- **Vision model:** `gemini-3-1-pro` (multimodal, best image reasoning)
- **Text models:** `gemini-3-5-flash` (near-Pro coding at Flash cost)
- **Runtime:** Vertex AI Agent Engine (`us-west1`)

---

## Repo structure

```
threejs-scene-agents/
├── threejs_scene_generator/        # Main ADK package (adk run target)
│   ├── __init__.py                 # Env setup + exposes root_agent
│   ├── agent.py                    # Pipeline wiring; defines root_agent
│   ├── config.py                   # VISION_MODEL, GENAI_MODEL env vars
│   └── sub_agents/
│       ├── vision/
│       │   ├── __init__.py
│       │   ├── vision_agent.py     # Agent 1 — before_model_callback for image injection
│       │   └── prompt.py           # VISION_PROMPT
│       ├── codegen/
│       │   ├── __init__.py
│       │   ├── codegen_agent.py    # Agent 2 — sets iteration=0 via after_agent_callback
│       │   └── prompt.py           # CODEGEN_PROMPT (uses {scene_description})
│       ├── validator/
│       │   ├── __init__.py
│       │   ├── validator_agent.py  # Agent 3 — uses set_validation_result tool
│       │   ├── tools.py            # set_validation_result — writes state, exits loop
│       │   └── prompt.py           # VALIDATOR_PROMPT (uses {threejs_code} etc.)
│       └── refinement/
│           ├── __init__.py
│           ├── refinement_agent.py # Agent 4 — increments iteration via after_agent_callback
│           └── prompt.py           # REFINEMENT_PROMPT (uses {threejs_code} etc.)
├── deploy.py                       # Creates or updates Agent Engine deployment
├── test_local.py                   # Runs pipeline locally via ADK Runner
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── CLAUDE.md                       # Developer commands and architecture summary
└── SPEC.md                         # This file
```

---

## Environment variables

```
# .env.example
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-west1
GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud/application_default_credentials.json
VISION_MODEL=gemini-3-1-pro
GENAI_MODEL=gemini-3-5-flash
AGENT_ENGINE_RESOURCE_NAME=          # Set after first deploy; triggers update instead of create
```

Local development uses `gcloud auth application-default login`.
Never commit credentials.

---

## Dependencies — `pyproject.toml`

```toml
[project]
name = "threejs-scene-agents"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "google-adk>=1.5.0",
    "google-cloud-aiplatform>=1.93.0",
    "python-dotenv>=1.0",
]
```

---

## Agent pipeline

### Overview

```
Input: { image: base64, mime_type: str, prompt: str }  — set in session state by caller

[SequentialAgent: scene_pipeline]  (root_agent in agent.py)
  Agent 1: VisionAgent        — analyses photo, produces scene_description JSON
  Agent 2: CodeGenAgent       — generates Three.js code from scene_description
  [LoopAgent: refine_loop, max_iterations=3]
    Agent 3: ValidatorAgent   — scores code 0-100, calls set_validation_result tool
    Agent 4: RefinementAgent  — rewrites failing sections based on feedback

Output (in session state): threejs_code, validation_score, validation_feedback
```

### Session state keys

| Key | Type | Set by | Read by |
|-----|------|--------|---------|
| `image` | str (base64) | caller | VisionAgent |
| `mime_type` | str | caller | VisionAgent |
| `prompt` | str | caller | VisionAgent |
| `scene_description` | str (JSON) | VisionAgent | CodeGenAgent, ValidatorAgent, RefinementAgent |
| `threejs_code` | str | CodeGenAgent, RefinementAgent | ValidatorAgent, RefinementAgent |
| `iteration` | int | CodeGenAgent (0), RefinementAgent (++) | ValidatorAgent, RefinementAgent |
| `validation_score` | int | ValidatorAgent (via tool) | caller, RefinementAgent |
| `validation_feedback` | str | ValidatorAgent (via tool) | RefinementAgent |

---

### Agent 1: VisionAgent (`LlmAgent`)

**File:** `sub_agents/vision/vision_agent.py`

**Model:** `config.VISION_MODEL` (default: `gemini-3-1-pro`)

**Input:** reads `image`, `mime_type`, `prompt` from session state

**Mechanism:** `before_model_callback` injects the base64 image as a multimodal
`Content` object directly into the LLM request. This is necessary because session
state substitution only works for text; images must be passed as typed `Part` objects.

**Output:** writes `scene_description` to session state via `output_key`:
```json
{
  "object": "brief description of the main subject",
  "geometry": "SphereGeometry | BoxGeometry | CylinderGeometry | TorusGeometry | custom",
  "colors": ["#hexcolor1", "#hexcolor2"],
  "material": "MeshStandardMaterial | MeshLambertMaterial | MeshPhongMaterial",
  "lighting": "warm | cool | dramatic | neutral",
  "animation": "rotate | float | orbit | pulse | none",
  "background": "#hexcolor or 'fog'",
  "environment": "ground_plane | minimal | dark"
}
```

---

### Agent 2: CodeGenAgent (`LlmAgent`)

**File:** `sub_agents/codegen/codegen_agent.py`

**Model:** `config.MODEL` (default: `gemini-3-5-flash`)

**Input:** `{scene_description}` substituted directly into `CODEGEN_PROMPT` at runtime
by ADK's instruction templating engine (one-pass `{key}` → `session.state[key]`).

**Output:**
- `output_key="threejs_code"` writes the generated JS to session state
- `after_agent_callback` sets `session.state["iteration"] = 0`

**The generated code must:**
- Target Three.js r128 exactly
- Contain zero `import` or `export` statements
- Define an `init(canvas)` function that returns a `dispose()` function
- Be executable as: `new Function('THREE', 'canvas', code)(THREE, canvasElement)`

---

### Agent 3: ValidatorAgent (`LlmAgent`) — inside LoopAgent

**File:** `sub_agents/validator/validator_agent.py`

**Model:** `config.MODEL` (default: `gemini-3-5-flash`)

**Input:** `{iteration}`, `{scene_description}`, `{threejs_code}` substituted into
`VALIDATOR_PROMPT` via ADK instruction templating.

**Tool:** `set_validation_result(score: int, feedback: str, tool_context: ToolContext)`
defined in `tools.py`. The agent calls this tool with its score and feedback after
analysis. The tool:
- Writes `validation_score` and `validation_feedback` to session state
- Sets `tool_context.actions.escalate = True` if `score >= 80` or `iteration >= 3`,
  which signals the LoopAgent to stop

**Why tool not callback:** Using a tool (matching the ADK sample pattern) is more
explicit and reliable than `after_agent_callback` — the LLM actively calls the exit
function, and `tool_context.actions.escalate` is the documented mechanism for loop
termination.

---

### Agent 4: RefinementAgent (`LlmAgent`) — inside LoopAgent

**File:** `sub_agents/refinement/refinement_agent.py`

**Model:** `config.MODEL` (default: `gemini-3-5-flash`)

**Input:** `{iteration}`, `{scene_description}`, `{validation_feedback}`,
`{threejs_code}` substituted into `REFINEMENT_PROMPT` via ADK instruction templating.

**Output:**
- `output_key="threejs_code"` writes improved code to session state
- `after_agent_callback` increments `session.state["iteration"]` by 1

---

### Pipeline wiring — `agent.py`

```python
from google.adk.agents import LoopAgent, SequentialAgent

refine_loop = LoopAgent(
    name="refine_loop",
    max_iterations=3,
    sub_agents=[validator_agent, refinement_agent],
)

root_agent = SequentialAgent(
    name="scene_pipeline",
    sub_agents=[vision_agent, codegen_agent, refine_loop],
)
```

`root_agent` is exposed from `threejs_scene_generator/__init__.py` for `adk run`.

---

### Instruction templating

ADK substitutes `{key}` patterns in agent instructions at runtime using
`session.state[key]`. The substitution is one-pass — values that themselves contain
`{...}` (e.g. JavaScript code with object literals) are safe because only the
template is scanned, not the substituted result.

VisionAgent does **not** use instruction templating for the image — images must be
injected as typed `Part` objects via `before_model_callback`.

---

## Deployment — `deploy.py`

Run once from a local machine with ADC credentials.
If `AGENT_ENGINE_RESOURCE_NAME` is set in `.env`, updates the existing deployment
instead of creating a new one.

```python
from threejs_scene_generator.agent import root_agent

engine = reasoning_engines.AgentEngine.create(
    agent_engine=root_agent,
    requirements=["google-adk>=1.5.0", "google-cloud-aiplatform>=1.93.0"],
    display_name="threejs-scene-generator",
)
print(f"AGENT_ENGINE_RESOURCE_NAME={engine.resource_name}")
```

---

## Local testing — `test_local.py`

```
uv run python test_local.py path/to/photo.jpg "make it dramatic"
```

Uses ADK's `Runner` + `InMemorySessionService` with `new_message=None` — the
pipeline is driven entirely by session state, not by a conversational user message.

---

## IAM requirements

The identity running `deploy.py` needs:
- `roles/aiplatform.admin` — to create/update Agent Engine deployments

The Cloud Run service account on `personal-website` needs:
- `roles/aiplatform.user` — to call `streamQuery` at runtime

---

## Key constraints

- **`uv` only** — no `pip` or `poetry`
- **No web server** — no FastAPI, Flask, or HTTP handler of any kind
- **No Docker** — Agent Engine handles containerisation
- **`max_iterations=3`** — hard cap on the refinement loop
- **Session state is the API** — agents communicate only via session state keys
- **Generated code targets Three.js r128** — validator prompt enforces this explicitly
- **No test suite** — `test_local.py` is an integration smoke test only

---

## Out of scope

- Web server or HTTP handler
- Docker or containerisation
- CI/CD (deploy is manual)
- Fine-tuning or training
- Storing generated scenes
- Any frontend code
