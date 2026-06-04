from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext

from ... import config
from .prompt import REFINEMENT_PROMPT


def _after_agent_callback(callback_context: CallbackContext) -> None:
    current = int(callback_context.state.get("iteration", 0))
    callback_context.state["iteration"] = current + 1
    return None


refinement_agent = LlmAgent(
    name="refinement_agent",
    model=config.MODEL,
    instruction=REFINEMENT_PROMPT,
    output_key="threejs_code",
    after_agent_callback=_after_agent_callback,
)
