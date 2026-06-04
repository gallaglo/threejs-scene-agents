from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext

from ... import config
from .prompt import CODEGEN_PROMPT


def _after_agent_callback(callback_context: CallbackContext) -> None:
    callback_context.state["iteration"] = 0
    return None


codegen_agent = LlmAgent(
    name="codegen_agent",
    model=config.MODEL,
    instruction=CODEGEN_PROMPT,
    output_key="threejs_code",
    after_agent_callback=_after_agent_callback,
)
