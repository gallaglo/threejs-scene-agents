from google.adk.tools import ToolContext


def set_validation_result(
    score: int,
    feedback: str,
    tool_context: ToolContext,
) -> dict:
    """Record the validation score and feedback. Exits the refinement loop if the score meets the threshold."""
    tool_context.state["validation_score"] = score
    tool_context.state["validation_feedback"] = feedback

    iteration = int(tool_context.state.get("iteration", 0))
    if score >= 80 or iteration >= 3:
        tool_context.actions.escalate = True
        return {
            "status": "done",
            "message": f"Score {score} meets threshold or iteration {iteration} reached limit. Exiting loop.",
        }
    return {
        "status": "continue",
        "message": f"Score {score} below threshold at iteration {iteration}. Proceeding to refinement.",
    }
