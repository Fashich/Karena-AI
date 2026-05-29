# Karena AI — Technical Specification

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `react` | `^19.0.0` | UI framework |
| `react-dom` | `^19.0.0` | React DOM renderer |
| `three` | `^0.172.0` | 3D engine for fluid sim, isometric stage, holographic grid |
| `@types/three` | `^0.172.0` | TypeScript types for Three.js |
| `gsap` | `^3.12.7` | Animation engine + ScrollTrigger plugin |
| `@studio-freight/lenis` | `^1.0.42` | Smooth scroll (lerp 0.1) |
| `splitting` | `^1.1.0` | Text character splitting for entrance animations |
| `vite` | `^6.0.0` | Build tool |
| `@vitejs/plugin-react` | `^4.3.0` | React Vite plugin |
| `tailwindcss` | `^4.0.0` | Utility-first CSS |
| `@tailwindcss/vite` | `^4.0.0` | Tailwind Vite integration |
| `typescript` | `^5.7.0` | Type safety |
| `@types/react` | `^19.0.0` | React type definitions |
| `@types/react-dom` | `^19.0.0` | React DOM type definitions |

GSAP plugins used (all free, registered once at app entry): `ScrollTrigger`.

Fonts loaded via Google Fonts CDN in `index.html`: `Space Grotesk` (400, 500) + `Inter` (400, 500).

---

## Component Inventory

### Layout (shared)

| Component | Source | Reuse |
|-----------|--------|-------|
| `Navigation` | Custom | Once — fixed global nav, transparent |
| `Footer` | Custom | Once — inverse color scheme |

### Sections (page-specific, used once each)

| Component | Source | Notes |
|-----------|--------|-------|
| `HeroSection` | Custom | Contains `FluidEngineBackground` + text overlay |
| `VisionSection` | Custom | Contains `OrbitMarquee` |
| `PlatformShowcase` | Custom | Contains `IsometricPlatformStage` |
| `IntelligenceSection` | Custom | Contains `NeuralCircuitSystem` + text overlay |
| `EnterpriseTrustSection` | Custom | Contains `HolographicMeshGrid` + scrolling text overlays |

### Reusable Components

| Component | Source | Reuse |
|-----------|--------|-------|
| `MagneticButton` | Custom | All CTA buttons — magnetic pull on hover via GSAP |
| `ScrollRevealText` | Custom | All section text blocks — fade-up entrance via GSAP ScrollTrigger |

### Core Effects (isolated canvas/shader systems)

| Component | Source | Notes |
|-----------|--------|-------|
| `FluidEngineBackground` | Custom (Three.js GPGPU) | Dual-pass ping-pong fluid sim → FBM warp display. Most complex system. |
| `NeuralCircuitSystem` | Custom (Canvas 2D) | Animated bezier path pulses with light packets |
| `HolographicMeshGrid` | Custom (Three.js fullscreen quad) | CRT scanlines + bayer dither + mouse-reveal grid |
| `IsometricPlatformStage` | Custom (Three.js) | Scroll-driven 3D card stack rotation |
| `OrbitMarquee` | Custom (CSS 3D) | Duplicated text rows in CSS 3D cylinder |

---

## Animation Implementation

| Animation | Library | Approach | Complexity |
|-----------|---------|----------|------------|
| FluidEngineBackground GPGPU sim | Three.js (raw) | Dual WebGLRenderTarget ping-pong, custom fluid + display shaders | **High** 🔒 |
| NeuralCircuitSystem | Canvas 2D (raw) | bezierCurveTo paths, radial gradient pulses, RAF loop | **High** 🔒 |
| HolographicMeshGrid | Three.js (raw) | Fullscreen quad with custom fragment shader (scanlines, bayer, grid) | **High** 🔒 |
| IsometricPlatformStage | Three.js + GSAP ScrollTrigger | Sticky container, scroll progress drives camera + card positions | **High** 🔒 |
| OrbitMarquee | CSS 3D transforms | perspective container, duplicated rows with translateX animation | Medium |
| Section text entrance reveals | GSAP ScrollTrigger | y: 30 → 0, opacity: 0 → 1, per text block | Low |
| Magnetic button hover | GSAP | Mousemove listener shifts button toward cursor | Low |
| Smooth scrolling | Lenis | Global init with lerp 0.1 | Low |
| Button hover states | CSS transitions | bg/border color transitions | Low |

---

## State & Logic Plan

### FluidEngineBackground — Visibility-aware GPU lifecycle

This is the heaviest GPU consumer. It must be **paused when off-screen** to free resources for downstream effects.

- Track visibility via IntersectionObserver on the HeroSection root. When observer reports `< 0.1` intersection ratio, cancel the RAF loop and do NOT resume until the user scrolls back into the hero.
- The fluid sim mouse coordinates (`iMouse`) need JS-side interpolation: `prevX = prevX * 0.9 + currentX * 0.1` (same for Y). Store this in a ref, update on `pointermove`, pass as uniform each frame.
- Both render targets must use `HalfFloatType` for fluid state precision. The display target uses a standard render target.

### NeuralCircuitSystem — Canvas 2D path generation

- Circuit paths are generated once on mount (not per-frame). `createCircuitPath(i, total, width, height)` produces a deterministic but randomized bezier path for each of 6-8 circuit lines.
- Each path stores an array of "pulse" objects: `{ progress: number, speed: number }`. Every frame, pulses advance by their speed. When `progress >= 1`, the pulse is removed.
- New pulses spawn at random intervals (0.3–1.5s) per path.
- The canvas uses a fade-trail technique: `fillRect` with `rgba(0,0,0,0.1)` instead of `clearRect`, creating motion trails.

### HolographicMeshGrid — Mouse uniform wiring

- Mouse position normalized to [0,1] range, passed as `u_mouse` uniform. Invert Y for WebGL coord space.
- The Bayer dither pattern must be implemented as an exact lookup table (16 values) per the shader spec — not a texture lookup.
- `u_image` uniform receives a texture loaded from the generated enterprise dashboard image.

### IsometricPlatformStage — Scroll progress binding

- Container: `position: sticky; top: 0; height: 100vh`. Parent wrapper has `height: 200vh` to create scroll travel distance.
- Use GSAP ScrollTrigger with `scrub: true` to map scroll progress (0→1) to camera position and card transforms.
- Camera moves from `[0, -5, 3]` to `[0, 1.2, 3]` with easing `cubic-bezier(0.19, 1, 0.22, 1)` — implement via GSAP's built-in easing or manual ease interpolation.
- Cards scale on Z-axis: `scaleZ = 1 + (0.8 * progress * (index + 1) / total)`. Opacity fades: `1 - (progress * 0.2)`.
- Three.js renderer uses `alpha: true` with `setClearColor(0x000000, 0)` so the section background shows through.

### Lenis + GSAP ScrollTrigger integration

- Initialize Lenis at app entry. On every Lenis `scroll` event, call `ScrollTrigger.update()` to keep GSAP in sync with the smooth-scrolled position.
- Use Lenis `raf` integration: Lenis.raf(time) called from a global requestAnimationFrame loop.

---

## Other Key Decisions

### Raw Three.js over React Three Fiber

All Three.js effects (FluidEngineBackground, HolographicMeshGrid, IsometricPlatformStage) use **raw Three.js** (not R3F). Reasons:
- GPGPU fluid sim requires manual render target ping-ponging and explicit render loop control — R3F's declarative model adds friction.
- Effects are isolated fullscreen canvases, not integrated 3D scenes with shared state.
- Direct shader string injection is cleaner without R3F's `<shaderMaterial>` abstraction overhead.

Each effect is a self-contained React component that creates its own `WebGLRenderer` and manages its own lifecycle (mount/unmount/resize).

### Image Assets

4 generated images required:
1. Dark data-center corridor (fluid background)
2. Enterprise AI analytics dashboard (isometric card 1)
3. Abstract neural network pattern (isometric card 2)
4. Security compliance dashboard (isometric card 3 + holographic grid background)

Loaded as Three.js textures via `TextureLoader`. Dashboard images should be ~1024px wide for texture quality without excessive VRAM.

### Mobile Considerations

- Fluid sim: on mobile, reduce fluid render target resolution by 0.5x for performance.
- Isometric stage: reduce card count from 3 to 1 on screens < 768px.
- Neural circuit: reduce path count from 8 to 4 on mobile.
- OrbitMarquee: reduce row count from 4 to 2 on mobile.

---

## Architecture Diagram

```
App (Lenis provider + ScrollTrigger setup)
├── Navigation (fixed, transparent)
├── HeroSection
│   ├── FluidEngineBackground (Three.js canvas, fullscreen, z-0)
│   └── HeroText (z-10, pointer-events-none)
├── VisionSection
│   └── OrbitMarquee (CSS 3D cylinder)
├── PlatformShowcase (sticky, 200vh wrapper)
│   └── IsometricPlatformStage (Three.js canvas, sticky inner)
├── IntelligenceSection
│   ├── NeuralCircuitSystem (Canvas 2D overlay, z-0)
│   └── SectionText (z-10)
├── EnterpriseTrustSection (300vh)
│   ├── HolographicMeshGrid (Three.js canvas, sticky/fixed, z-0)
│   └── ScrollingTextOverlays (z-10, GSAP-triggered fade in/out)
└── Footer (solid white)
```
