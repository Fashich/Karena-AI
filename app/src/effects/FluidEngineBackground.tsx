import { useRef, useEffect } from 'react';
import * as THREE from 'three';

const vertexShader = `
varying vec2 v_uv;
void main() {
  v_uv = uv;
  gl_Position = vec4(position, 1.0);
}
`;

const fluidFragmentShader = `
precision mediump float;

uniform sampler2D uPrevState;
uniform vec4 iMouse;
uniform vec2 uResolution;
uniform float uBrushSize;
uniform float uBrushStrength;
uniform float uFluidDecay;
uniform float uTrailLength;
uniform float uStopDecay;

varying vec2 v_uv;

#define s uBrushStrength
#define b uBrushSize
#define f uFluidDecay
#define t uTrailLength
#define p uStopDecay
#define SIM_SCALE 0.0003
#define PRESSURE_LIMIT 0.3
#define P_R 0.00014
#define P_B 0.0002

vec3 decode(vec3 c) {
  return (c - 0.5) * 0.8;
}

vec3 encode(vec3 v) {
  v = clamp(v, -0.4, 0.4);
  return v / 0.8 + 0.5;
}

float lineDistance(vec2 p, vec2 a, vec2 b) {
  vec2 ab = b - a;
  float l2 = dot(ab, ab);
  if (l2 < 0.0001) return distance(p, a);
  float t = clamp(dot(p - a, ab) / l2, 0.0, 1.0);
  return distance(p, a + t * ab);
}

void main() {
  vec2 pixel = v_uv * uResolution;
  vec3 prev = texture2D(uPrevState, v_uv).rgb;
  vec2 vel = decode(prev).xy;

  vec2 dx = vec2(1.0, 0.0);
  vec2 dy = vec2(0.0, 1.0);

  vec2 vel_r = decode(texture2D(uPrevState, v_uv + dx / uResolution).rgb).xy;
  vec2 vel_l = decode(texture2D(uPrevState, v_uv - dx / uResolution).rgb).xy;
  vec2 vel_u = decode(texture2D(uPrevState, v_uv + dy / uResolution).rgb).xy;
  vec2 vel_d = decode(texture2D(uPrevState, v_uv - dy / uResolution).rgb).xy;

  vec2 diffusion = (vel_r + vel_l + vel_u + vel_d - 4.0 * vel) * 0.25;
  vel += diffusion * 0.2;
  vel *= f;

  vec2 mousePos = iMouse.xy;
  vec2 mousePrev = iMouse.zw;
  vec2 motion = mousePos - mousePrev;
  float motionLen = length(motion);
  vec2 motionDir = motionLen > 0.0001 ? motion / motionLen : vec2(0.0);

  float qLine = lineDistance(pixel, mousePos, mousePrev);
  float qPoint = distance(pixel, mousePos);
  float q = mix(qLine, qPoint, 0.4);

  float brushSizeFactor = 2.2e-4 / b;
  float strengthFactor = 0.03 * s;

  float brush = exp(-q * q * brushSizeFactor);
  brush *= strengthFactor;

  float idleTime = distance(mousePos, mousePrev);
  float idleFade = exp(-idleTime * 0.03 * p);

  vel += brush * motionDir * motionLen * 0.03 * SIM_SCALE * 10000.0 * idleFade;

  float dragR = exp(-qPoint * qPoint * brushSizeFactor * 0.5) * 0.5;

  float pr_r = vel_r.x - vel.x;
  float pr_l = vel_l.x - vel.x;
  float pr_u = vel_u.y - vel.y;
  float pr_d = vel_d.y - vel.y;
  float pr = (pr_r - pr_l + pr_u - pr_d) * 100.0 * P_R;
  pr = clamp(pr, -PRESSURE_LIMIT, PRESSURE_LIMIT);

  float push = exp(-abs(pr) * 4.0e-4);
  vec2 dir = normalize(pixel - mousePos + vec2(1e-5));
  vel += push * dir * pr * dragR * P_B * 300.0;

  vel.x = clamp(vel.x, -0.4, 0.4);
  vel.y = clamp(vel.y, -0.4, 0.4);

  float tFactor = clamp(length(vel) * 200.0 * t, 0.0, 0.3);
  vel *= max(1.0 - tFactor, 0.0);

  gl_FragColor = vec4(encode(vec3(vel, 0.0)), 1.0);
}
`;

const displayFragmentShader = `
precision mediump float;

uniform float u_time;
uniform sampler2D u_fluid;
uniform sampler2D uBackground;
uniform float uDistortionAmount;

varying vec2 v_uv;

float random(vec2 st) {
  return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
}

vec2 rotate(vec2 uv, float angle) {
  float s = sin(angle);
  float c = cos(angle);
  return mat2(c, -s, s, c) * (uv - 0.5) + 0.5;
}

void main() {
  vec2 uv = v_uv;
  vec3 fluid = texture2D(u_fluid, v_uv).rgb;
  vec2 fluidVel = (fluid.xy - 0.5) * 0.8;
  float fluidDistort = length(fluidVel) * uDistortionAmount;

  float angle = u_time * 0.1 + fluidDistort * 1.5;
  uv = rotate(uv, angle);

  uv += vec2(0.5 * sin(u_time * 0.05 + uv.y * 2.0), 0.3 * cos(u_time * 0.05 + uv.x * 1.5));
  uv += vec2(0.2 * sin(u_time * 0.1 + uv.y * 5.0), 0.2 * cos(u_time * 0.1 + uv.x * 4.0));
  uv += vec2(0.1 * sin(u_time * 0.2 + uv.y * 10.0), 0.1 * cos(u_time * 0.2 + uv.x * 8.0));

  uv = floor(uv * 50.0) / 50.0;

  uv.x += fluid.x * uDistortionAmount;
  uv.y += fluid.y * uDistortionAmount;

  float grain = random(uv * u_time) * 0.15;
  vec3 color = texture2D(uBackground, uv).rgb;
  color += grain;

  gl_FragColor = vec4(color, 1.0);
}
`;

interface FluidEngineBackgroundProps {
  isVisible: boolean;
}

export default function FluidEngineBackground({ isVisible }: FluidEngineBackgroundProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const rafRef = useRef<number>(0);
  const mouseRef = useRef({ x: 0, y: 0, px: 0, py: 0 });
  const timeRef = useRef(0);

  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const width = container.offsetWidth || window.innerWidth;
    const height = container.offsetHeight || window.innerHeight;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: false, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Camera
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    // Scene for fluid pass
    const fluidScene = new THREE.Scene();
    const fluidGeometry = new THREE.PlaneGeometry(2, 2);

    // Fluid render targets (ping-pong)
    const rtOptions: THREE.RenderTargetOptions = {
      type: THREE.HalfFloatType,
      format: THREE.RGBAFormat,
      minFilter: THREE.LinearFilter,
      magFilter: THREE.LinearFilter,
      wrapS: THREE.ClampToEdgeWrapping,
      wrapT: THREE.ClampToEdgeWrapping,
    };
    const simW = Math.floor(width * 0.5);
    const simH = Math.floor(height * 0.5);
    let fluidA = new THREE.WebGLRenderTarget(simW, simH, rtOptions);
    let fluidB = new THREE.WebGLRenderTarget(simW, simH, rtOptions);

    // Display render target
    const displayRT = new THREE.WebGLRenderTarget(width, height, {
      minFilter: THREE.LinearFilter,
      magFilter: THREE.LinearFilter,
      format: THREE.RGBAFormat,
    });

    // Load background texture
    const textureLoader = new THREE.TextureLoader();
    const bgTexture = textureLoader.load('/assets/data-center.jpg');
    bgTexture.minFilter = THREE.LinearFilter;
    bgTexture.magFilter = THREE.LinearFilter;

    // Fluid material
    const fluidMaterial = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader: fluidFragmentShader,
      uniforms: {
        uPrevState: { value: fluidA.texture },
        iMouse: { value: new THREE.Vector4(0, 0, 0, 0) },
        uResolution: { value: new THREE.Vector2(simW, simH) },
        uBrushSize: { value: 0.25 },
        uBrushStrength: { value: 0.2 },
        uFluidDecay: { value: 0.98 },
        uTrailLength: { value: 1.0 },
        uStopDecay: { value: 1.0 },
      },
    });
    const fluidMesh = new THREE.Mesh(fluidGeometry, fluidMaterial);
    fluidScene.add(fluidMesh);

    // Display scene
    const displayScene = new THREE.Scene();
    const displayMaterial = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader: displayFragmentShader,
      uniforms: {
        u_time: { value: 0 },
        u_fluid: { value: fluidA.texture },
        uBackground: { value: bgTexture },
        uDistortionAmount: { value: 1.8 },
      },
    });
    const displayMesh = new THREE.Mesh(fluidGeometry, displayMaterial);
    displayScene.add(displayMesh);

    // Mouse handling
    const handlePointerMove = (e: PointerEvent) => {
      const rect = container.getBoundingClientRect();
      const nx = (e.clientX - rect.left) / rect.width;
      const ny = 1.0 - (e.clientY - rect.top) / rect.height;
      mouseRef.current.x = nx;
      mouseRef.current.y = ny;
    };
    window.addEventListener('pointermove', handlePointerMove);

    // Animation loop
    const animate = () => {
      rafRef.current = requestAnimationFrame(animate);

      // Interpolate mouse
      const m = mouseRef.current;
      m.px = m.px * 0.9 + m.x * 0.1;
      m.py = m.py * 0.9 + m.y * 0.1;

      const now = performance.now();
      timeRef.current = now;

      // Fluid pass: render into fluidA
      fluidMaterial.uniforms.uPrevState.value = fluidA.texture;
      fluidMaterial.uniforms.iMouse.value.set(
        m.x * simW, m.y * simH, m.px * simW, m.py * simH
      );
      renderer.setRenderTarget(fluidA);
      renderer.render(fluidScene, camera);

      // Display pass: render into displayRT
      displayMaterial.uniforms.u_fluid.value = fluidA.texture;
      displayMaterial.uniforms.u_time.value = now * 0.001;
      renderer.setRenderTarget(displayRT);
      renderer.render(displayScene, camera);

      // Copy displayRT to uBackground for feedback
      renderer.copyTextureToTexture(
        displayRT.texture,
        displayMaterial.uniforms.uBackground.value as THREE.Texture
      );

      // Render display to screen
      renderer.setRenderTarget(null);
      renderer.render(displayScene, camera);
    };

    animate();

    // Handle resize
    const handleResize = () => {
      const w = container.offsetWidth || window.innerWidth;
      const h = container.offsetHeight || window.innerHeight;
      renderer.setSize(w, h);
      displayRT.setSize(w, h);
      const sw = Math.floor(w * 0.5);
      const sh = Math.floor(h * 0.5);
      const newA = new THREE.WebGLRenderTarget(sw, sh, rtOptions);
      const newB = new THREE.WebGLRenderTarget(sw, sh, rtOptions);
      fluidA.dispose();
      fluidB.dispose();
      fluidA = newA;
      fluidB = newB;
      fluidMaterial.uniforms.uResolution.value.set(sw, sh);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('resize', handleResize);
      fluidA.dispose();
      fluidB.dispose();
      displayRT.dispose();
      fluidGeometry.dispose();
      fluidMaterial.dispose();
      displayMaterial.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  // Pause/resume based on visibility
  useEffect(() => {
    if (!rendererRef.current) return;
    if (!isVisible) {
      cancelAnimationFrame(rafRef.current);
    }
  }, [isVisible]);

  return (
    <div
      ref={containerRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 0,
      }}
    />
  );
}
