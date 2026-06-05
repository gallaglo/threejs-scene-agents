import base64

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai.types import Content, Part

from ... import config
from .prompt import VISION_PROMPT


def _before_model_callback(callback_context: CallbackContext, llm_request) -> None:
    state = callback_context.state
    image_b64 = state.get("image", "")
    mime_type = state.get("mime_type", "image/jpeg")
    user_prompt = state.get("prompt", "")

    if image_b64:
        image_bytes = base64.b64decode(image_b64)
        text = user_prompt or "Analyze this image for Three.js scene generation."
        llm_request.contents = [
            Content(
                role="user",
                parts=[
                    Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    Part(text=text),
                ],
            )
        ]
    elif user_prompt:
        llm_request.contents = [
            Content(
                role="user",
                parts=[Part(text=user_prompt)],
            )
        ]
    return None


vision_agent = LlmAgent(
    name="vision_agent",
    model=config.VISION_MODEL,
    instruction=VISION_PROMPT,
    output_key="scene_description",
    before_model_callback=_before_model_callback,
)
