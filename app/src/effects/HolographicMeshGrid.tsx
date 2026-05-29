import { useRef, useEffect } from 'react';
import * as THREE from 'three';

const vertexShader = `
varying vec2 v_uv;
void main() {
  v_uv = uv;
  gl_Position = vec4(position, 1.0);
}
`;

const fragmentShader = `
precision mediump float;

uniform float u_time;
uniform vec2 u_mouse;
uniform vec2 u_resolution;
uniform sampler2D u_image;

varying vec2 v_uv;

#define PI 3.14159265359

float scanlines(vec2 uv, float t) {
  float y = uv.y * u_resolution.y;
  float scanY = y + t * 5.0;
  return pow(sin(scanY * PI * 0.5), 0.5);
}

float bayer(vec2 uv) {
  vec2 coord = floor(mod(uv * u_resolution, 4.0));
  float idx = coord.x + coord.y * 4.0;
  if (idx == 0.0) return 0.0 / 16.0;
  if (idx == 1.0) return 12.0 / 16.0;
  if (idx == 2.0) return 3.0 / 16.0;
  if (idx == 3.0) return 15.0 / 16.0;
  if (idx == 4.0) return 8.0 / 16.0;
  if (idx == 5.0) return 4.0 / 16.0;
  if (idx == 6.0) return 11.0 / 16.0;
  if (idx == 7.0) return 7.0 / 16.0;
  if (idx == 8.0) return 2.0 / 16.0;
  if (idx == 9.0) return 14.0 / 16.0;
  if (idx == 10.0) return 1.0 / 16.0;
  if (idx == 11.0) return 13.0 / 16.0;
  if (idx == 12.0) return 10.0 / 16.0;
  if (idx == 13.0) return 6.0 / 16.0;
  if (idx == 14.0) return 9.0 / 16.0;
  if (idx == 15.0) return 5.0 / 16.0;
  return 0.5;
}

float grid(vec2 uv) {
  uv = floor(uv * 25.0) / 25.0;
  float g = step(0.98, fract(uv.x * 25.0)) + step(0.98, fract(uv.y * 25.0));
  return clamp(g, 0.0, 1.0);
}

float holo(vec2 uv, float t) {
  float d = length(uv - vec2(0.5));
  return pow(1.0 - d, 2.5) * (sin(t * 0.8) * 0.5 + 0.5) * 0.6;
}

void main() {
  vec2 uv = gl_FragCoord.xy / u_resolution;
  vec2 m = vec2(u_mouse.x / u_resolution.x, 1.0 - u_mouse.y / u_resolution.y);
  float dist = distance(uv, m);
  float gridFactor = grid(uv);

  vec3 color = vec3(0.02, 0.02, 0.03);
  color += gridFactor * 0.05;
  color += texture2D(u_image, uv).rgb * 0.3;
  color += vec3(0.015, 0.02, 0.03) * scanlines(uv, u_time);
  color += vec3(0.0, 0.7, 1.0) * holo(uv, u_time);

  float mask = smoothstep(0.25, 0.0, dist);
  mask += smoothstep(0.01, 0.0, dist);
  mask = clamp(mask, 0.0, 1.0);

  color *= 1.0 + mask * 0.7;

  float dither = bayer(gl_FragCoord.xy);
  color += dither * 0.05;

  color *= smoothstep(1.2, 0.3, length(uv - 0.5));

  gl_FragColor = vec4(color, 1.0);
}
`;

export default function HolographicMeshGrid() {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const rafRef = useRef<number>(0);
  const mouseRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const width = container.offsetWidth || window.innerWidth;
    const height = container.offsetHeight || window.innerHeight;

    const renderer = new THREE.WebGLRenderer({ antialias: false, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    const scene = new THREE.Scene();
    const geometry = new THREE.PlaneGeometry(2, 2);

    const textureLoader = new THREE.TextureLoader();
    const imgTexture = textureLoader.load('/assets/dashboard-security.jpg');
    imgTexture.minFilter = THREE.LinearFilter;
    imgTexture.magFilter = THREE.LinearFilter;

    const material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms: {
        u_time: { value: 0 },
        u_mouse: { value: new THREE.Vector2(width / 2, height / 2) },
        u_resolution: { value: new THREE.Vector2(width, height) },
        u_image: { value: imgTexture },
      },
    });

    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    const handlePointerMove = (e: PointerEvent) => {
      const rect = container.getBoundingClientRect();
      mouseRef.current.x = (e.clientX - rect.left) * (window.devicePixelRatio);
      mouseRef.current.y = (e.clientY - rect.top) * (window.devicePixelRatio);
    };
    window.addEventListener('pointermove', handlePointerMove);

    const animate = () => {
      rafRef.current = requestAnimationFrame(animate);
      material.uniforms.u_time.value = performance.now() * 0.001;
      material.uniforms.u_mouse.value.set(mouseRef.current.x, mouseRef.current.y);
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      const w = container.offsetWidth || window.innerWidth;
      const h = container.offsetHeight || window.innerHeight;
      renderer.setSize(w, h);
      material.uniforms.u_resolution.value.set(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('resize', handleResize);
      geometry.dispose();
      material.dispose();
      imgTexture.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        position: 'sticky',
        top: 0,
        width: '100%',
        height: '100vh',
        zIndex: 0,
      }}
    />
  );
}
