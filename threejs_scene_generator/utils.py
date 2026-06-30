import re
from google.adk.agents.callback_context import CallbackContext


def clean_code_callback(callback_context: CallbackContext) -> None:
    """Strips markdown code fences and trims whitespace from the generated threejs_code."""
    code = callback_context.state.get("threejs_code", "")
    if not code:
        return

    code = code.strip()
    # Strip markdown code fences if present
    match = re.match(r"^```[a-zA-Z]*\n([\s\S]*?)\n```$", code)
    if match:
        code = match.group(1).strip()
    else:
        # Also clean up unclosed/partially generated fences
        code = re.sub(r"^```[a-zA-Z]*\s*", "", code)
        code = re.sub(r"\s*```$", "", code)

    callback_context.state["threejs_code"] = code.strip()
