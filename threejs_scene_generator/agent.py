import re

from google.adk import Context, Workflow
from google.adk.workflow import Edge, FunctionNode, START

from .sub_agents.codegen import codegen_agent
from .sub_agents.refinement import refinement_agent
from .sub_agents.validator import validator_agent
from .sub_agents.vision import vision_agent

_BANNED_APIS = ["CapsuleGeometry", "RoundedBoxGeometry", "WebGPURenderer"]

_BANNED_API_FIXES = {
    "CapsuleGeometry": (
        "Replace THREE.CapsuleGeometry — it does not exist in Three.js r128. "
        "Use a CylinderGeometry capped with two SphereGeometry halves instead."
    ),
    "RoundedBoxGeometry": (
        "Replace THREE.RoundedBoxGeometry — it does not exist in Three.js r128. "
        "Use a plain BoxGeometry or combine geometries from the r128 API."
    ),
    "WebGPURenderer": (
        "Replace THREE.WebGPURenderer — it does not exist in Three.js r128. "
        "Use THREE.WebGLRenderer instead."
    ),
}


def _init_state(ctx: Context) -> None:
    if "threejs_code" not in ctx.state:
        ctx.state["threejs_code"] = ""
    ctx.state["iteration"] = 0


def _increment_iteration(ctx: Context) -> None:
    ctx.state["iteration"] = int(ctx.state.get("iteration", 0)) + 1


def _static_validation_check(ctx: Context) -> str | None:
    code = ctx.state.get("threejs_code", "")
    failures = []

    # 1. Banned API checks
    found_banned = [api for api in _BANNED_APIS if api in code]
    for api in found_banned:
        failures.append(_BANNED_API_FIXES[api])

    # 2. Structural/Syntax checks
    if re.search(r"\.parameters\b", code):
        failures.append(
            "Do not use .parameters (e.g., geometry.parameters) to read dimensions. "
            "Instead, store the dimensions (width, height, radius, etc.) in local variables "
            "when instantiating the geometry, and reference those variables directly."
        )

    # 3. Uninitialized array/variable checks
    array_methods = ["shift", "pop", "push", "unshift", "forEach", "map", "filter", "find", "reduce"]
    pattern = r"\b([a-zA-Z0-9_$]+)\.(" + "|".join(array_methods) + r")\("
    matches = re.findall(pattern, code)
    checked_vars = set()
    for var_name, method in matches:
        if var_name in checked_vars:
            continue
        checked_vars.add(var_name)
        
        # Check if the variable is declared/initialized
        has_assignment = re.search(r"\b" + re.escape(var_name) + r"\s*=", code)
        is_param = re.search(r"function\s*\w*\s*\([^)]*\b" + re.escape(var_name) + r"\b", code)
        is_arrow_param = re.search(r"\(\s*[^)]*\b" + re.escape(var_name) + r"\b[^)]*\)\s*=>", code) or re.search(r"\b" + re.escape(var_name) + r"\s*=>", code)
        
        if not (has_assignment or is_param or is_arrow_param):
            failures.append(
                f"Variable '{var_name}' is used with .{method}() but is never initialized. "
                f"Declare and initialize it (e.g., const {var_name} = [];) before calling array methods."
            )

    if not re.search(r"\bfunction\s+init\s*\(|(?:const|let|var)\s+init\s*=", code):
        failures.append(
            "Define an init() function that sets up the scene and returns a dispose function."
        )

    if re.search(r"^\s*(?:import|export)\s", code, re.MULTILINE):
        failures.append(
            "Remove all import and export statements — the script runs in a plain <script> tag "
            "with Three.js available as THREE."
        )

    if "renderer.dispose()" not in code:
        failures.append(
            "Add renderer.dispose() inside the dispose function returned by init()."
        )

    if "cancelAnimationFrame" not in code:
        failures.append(
            "Add cancelAnimationFrame(animFrameId) inside the dispose function. "
            "Store the requestAnimationFrame return value in a variable and cancel it in dispose."
        )

    if failures:
        iteration = int(ctx.state.get("iteration", 0))
        if iteration >= 3:
            ctx.state["validation_score"] = 0
            ctx.state["validation_feedback"] = (
                f"Failed static checks: {len(failures)} issues remaining. Max iterations reached."
            )
            ctx.state["refinement_targets"] = "\n".join(
                f"{i + 1}. {t}" for i, t in enumerate(failures)
            )
            return "done"

        ctx.state["refinement_targets"] = "\n".join(
            f"{i + 1}. {t}" for i, t in enumerate(failures)
        )
        ctx.state["richness_feedback"] = ""
        ctx.state["animation_feedback"] = ""
        return "fail"

    return "pass"


init_state = FunctionNode(func=_init_state, name="init_state")
increment_iteration = FunctionNode(func=_increment_iteration, name="increment_iteration")
static_validation_check = FunctionNode(func=_static_validation_check, name="static_validation_check")

root_agent = Workflow(
    name="scene_pipeline",
    edges=[
        (START, vision_agent, init_state, codegen_agent, static_validation_check),
        Edge(from_node=static_validation_check, to_node=refinement_agent, route="fail"),
        Edge(from_node=static_validation_check, to_node=validator_agent, route="pass"),
        Edge(from_node=validator_agent, to_node=refinement_agent, route="continue"),
        Edge(from_node=refinement_agent, to_node=increment_iteration),
        Edge(from_node=increment_iteration, to_node=static_validation_check),
    ],
)
