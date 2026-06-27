from google.adk import Context, Workflow
from google.adk.workflow import Edge, FunctionNode, START

from .sub_agents.codegen import codegen_agent
from .sub_agents.refinement import refinement_agent
from .sub_agents.validator import validator_agent
from .sub_agents.vision import vision_agent


def _init_state(ctx: Context) -> None:
    if "threejs_code" not in ctx.state:
        ctx.state["threejs_code"] = ""
    ctx.state["iteration"] = 0


def _increment_iteration(ctx: Context) -> None:
    ctx.state["iteration"] = int(ctx.state.get("iteration", 0)) + 1


init_state = FunctionNode(func=_init_state, name="init_state")
increment_iteration = FunctionNode(func=_increment_iteration, name="increment_iteration")

root_agent = Workflow(
    name="scene_pipeline",
    edges=[
        (START, vision_agent, init_state, codegen_agent, validator_agent),
        Edge(from_node=validator_agent, to_node=refinement_agent, route="continue"),
        Edge(from_node=refinement_agent, to_node=increment_iteration),
        Edge(from_node=increment_iteration, to_node=validator_agent),
    ],
)
