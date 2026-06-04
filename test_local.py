import asyncio
import base64
import sys
from pathlib import Path

from threejs_scene_generator.agent import root_agent


async def test(image_path: str, prompt: str = "") -> None:
    image_bytes = Path(image_path).read_bytes()
    b64 = base64.b64encode(image_bytes).decode()
    mime = "image/jpeg"  # adjust as needed

    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="test",
        session_service=session_service,
    )
    session = await session_service.create_session(
        app_name="test",
        user_id="local",
        state={"image": b64, "mime_type": mime, "prompt": prompt},
    )

    async for event in runner.run_async(
        user_id="local",
        session_id=session.id,
        new_message=None,
    ):
        print(event)

    final = await session_service.get_session(
        app_name="test", user_id="local", session_id=session.id
    )
    print("\n--- Final Three.js code ---")
    print(final.state.get("threejs_code", "NOT GENERATED"))
    print(f"\nScore: {final.state.get('validation_score')}")
    print(f"Feedback: {final.state.get('validation_feedback')}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "test_image.jpg"
    prompt = sys.argv[2] if len(sys.argv) > 2 else ""
    asyncio.run(test(path, prompt))
