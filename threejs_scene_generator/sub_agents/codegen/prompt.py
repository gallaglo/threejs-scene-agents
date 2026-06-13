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

Scene description:
{scene_description}

Existing Three.js code (empty on first generation):
{threejs_code}

---

PASS 1 — Write a scene brief as a comment block at the very top of the output, before any code:

// SCENE BRIEF
// Hero moment: [the one visually memorable element and why]
// Depth layers: [background → midground → foreground elements]
// Signature animation: [the one primary animation; everything else is subtle]
// Anti-defaults check:
//   - NOT a single object in an empty void
//   - NOT everything rotating on all axes simultaneously
//   - NOT uniform grey/black fog with no sky treatment
//   - NOT only ambient + directional light with no color temperature
// Palette: [4–6 named hex values]
// Atmosphere: [sky treatment, fog rationale, light color temperature]

PASS 2 — Write the Three.js code immediately after the brief, deriving every color, light, and animation decision from it.

---

Mandatory scene requirements:
- At least 3 depth layers (background, midground, foreground)
- At least 2 independently animated elements beyond the hero
- An atmospheric treatment: sky gradient sphere, fog, or colored light temperature — not a plain black background
- A ground plane, water plane, or equivalent surface — no object floating in a void
- Secondary elements must each have their own subtle animation (cloud drift, water shimmer, foliage sway)
- Use LambertMaterial or PhongMaterial for most elements; reserve MeshStandardMaterial for the hero only
- Spend boldness in one place: the hero animation is the most elaborate; everything else is quiet and supportive
- scene_complexity "minimal" → precision over quantity; "rich" → build every layer fully

Three.js AI default patterns to actively avoid:
1. A single SphereGeometry or BoxGeometry on a black background with rotation.x += 0.01
2. AmbientLight + DirectionalLight only, both pure white, no color temperature
3. A flat PlaneGeometry ground with a GridHelper as the only visual texture
4. OrbitControls as a substitute for any designed camera behavior
5. All objects positioned at (0, 0, 0) with no spatial composition

The init(canvas) function must:
- Accept a raw HTMLCanvasElement
- Create a WebGLRenderer passing canvas as the canvas option (not appended to the DOM)
- Use canvas.width / canvas.height for camera aspect ratio and renderer size
- Set camera position and lookAt from the scene description camera field
- Build all geometry, materials, and lights procedurally from the scene description
- Start a requestAnimationFrame animation loop
- Return a synchronous dispose() function that calls renderer.dispose() and cancels the animation frame via cancelAnimationFrame

The code must be executable as:
  new Function('THREE', 'canvas', code)(THREE, canvasElement)

Multi-turn behavior:
- If existing code is non-empty AND scene_description starts with MODIFICATION:, treat this as a targeted edit. Start from the existing code and apply only the described changes. Return the complete updated code.
- If existing code is empty, generate the full scene from scratch based on scene_description.

Output only the JavaScript code (starting with the // SCENE BRIEF comment block). No markdown, no explanation.
"""
