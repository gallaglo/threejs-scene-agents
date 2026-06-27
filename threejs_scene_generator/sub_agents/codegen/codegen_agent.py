from google.adk.agents import LlmAgent

from ... import config
from .prompt import CODEGEN_PROMPT

codegen_agent = LlmAgent(
    name="codegen_agent",
    model=config.MODEL,
    instruction=CODEGEN_PROMPT,
    output_key="threejs_code",
)
