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


def _static_check(ctx: Context) -> str | None:
    code = ctx.state.get("threejs_code", "")
    failures = []

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
        ctx.state["refinement_targets"] = failures
        ctx.state["richness_feedback"] = ""
        ctx.state["animation_feedback"] = ""
        return "fail"
    return None


def _banned_api_check(ctx: Context) -> str | None:
    code = ctx.state.get("threejs_code", "")
    found = [api for api in _BANNED_APIS if api in code]
    if found:
        ctx.state["refinement_targets"] = [_BANNED_API_FIXES[api] for api in found]
        ctx.state["richness_feedback"] = ""
        ctx.state["animation_feedback"] = ""
        return "fail"
    return None


init_state = FunctionNode(func=_init_state, name="init_state")
increment_iteration = FunctionNode(func=_increment_iteration, name="increment_iteration")
static_check = FunctionNode(func=_static_check, name="static_check")
banned_api_check = FunctionNode(func=_banned_api_check, name="banned_api_check")

root_agent = Workflow(
    name="scene_pipeline",
    edges=[
        (START, vision_agent, init_state, codegen_agent, banned_api_check),
        Edge(from_node=banned_api_check, to_node=refinement_agent, route="fail"),
        Edge(from_node=banned_api_check, to_node=static_check),
        Edge(from_node=static_check, to_node=refinement_agent, route="fail"),
        Edge(from_node=static_check, to_node=validator_agent),
        Edge(from_node=validator_agent, to_node=refinement_agent, route="continue"),
        Edge(from_node=refinement_agent, to_node=increment_iteration),
        Edge(from_node=increment_iteration, to_node=banned_api_check),
    ],
)
