CODEGEN_PROMPT = """
You are generating Three.js r128 JavaScript code. Rules that must never be broken:
1. No import or export statements of any kind.
2. No ES module syntax.
3. Define a function called init that accepts one argument: a canvas element.
4. init must return a dispose function that calls renderer.dispose() and cancels the animation frame.
5. THREE is available as a global variable — do not declare it.
6. Only use APIs that exist in Three.js r128. Do not use APIs introduced after r128.
7. Pass canvas to the renderer constructor as the canvas option — do not call document.body.appendChild.
8. Use canvas.width and canvas.height for sizing — do not use window.innerWidth or window.innerHeight.
Output only the JavaScript code. No markdown, no explanation.

Scene description:
{scene_description}

Existing Three.js code (empty on first generation):
{threejs_code}

The init(canvas) function must:
- Accept a raw HTMLCanvasElement
- Create a WebGLRenderer passing canvas as the canvas option (not appended to the DOM)
- Use canvas.width / canvas.height for camera aspect ratio and renderer size
- Create a PerspectiveCamera and Scene
- Build all geometry, materials, and lights procedurally from the scene description
- Start a requestAnimationFrame animation loop matching the "animation" field
- Return a synchronous dispose() function that calls renderer.dispose() and cancels the animation frame via cancelAnimationFrame

The code must be executable as:
  new Function('THREE', 'canvas', code)(THREE, canvasElement)

Multi-turn behavior:
- If existing code is non-empty AND scene_description starts with MODIFICATION:, treat this as a targeted edit. Start from the existing code and apply only the described changes. Return the complete updated code.
- If existing code is empty, generate the full scene from scratch based on scene_description.

Use the colors from the scene description for materials. Match the lighting type (warm/cool/dramatic/neutral) with appropriate light colors and intensities. Match the geometry type exactly. Implement the animation type exactly as specified.
"""
