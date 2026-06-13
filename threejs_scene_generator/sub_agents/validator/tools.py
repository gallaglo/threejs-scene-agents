from google.adk.tools import ToolContext


def set_validation_result(
    score: int,
    correctness_score: int,
    richness_score: int,
    animation_score: int,
    hygiene_score: int,
    richness_feedback: str,
    animation_feedback: str,
    refinement_targets: list[str],
    tool_context: ToolContext,
) -> dict:
    """Record the validation scores and refinement targets. Exits the refinement loop if the score meets the threshold."""
    tool_context.state["validation_score"] = score
    tool_context.state["validation_feedback"] = (
        f"Correctness: {correctness_score}/40. "
        f"Visual richness: {richness_score}/30. "
        f"Animation: {animation_score}/20. "
        f"Hygiene: {hygiene_score}/10."
    )
    tool_context.state["richness_feedback"] = richness_feedback
    tool_context.state["animation_feedback"] = animation_feedback
    tool_context.state["refinement_targets"] = "\n".join(
        f"{i + 1}. {t}" for i, t in enumerate(refinement_targets)
    )

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
