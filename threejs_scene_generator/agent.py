from google.adk import Workflow
from google.adk.workflow import Edge, START

from .sub_agents.codegen import codegen_agent
from .sub_agents.refinement import refinement_agent
from .sub_agents.validator import validator_agent
from .sub_agents.vision import vision_agent

root_agent = Workflow(
    name="scene_pipeline",
    edges=[
        (START, vision_agent, codegen_agent, validator_agent),
        Edge(from_node=validator_agent, to_node=refinement_agent, route="continue"),
        Edge(from_node=refinement_agent, to_node=validator_agent),
    ],
)
