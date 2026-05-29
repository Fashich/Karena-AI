import { useRef, useEffect } from 'react';
import * as THREE from 'three';

export default function IsometricPlatformStage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const rafRef = useRef<number>(0);
  const progressRef = useRef(0);

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const width = container.offsetWidth || window.innerWidth;
    const height = container.offsetHeight || window.innerHeight;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, -5, 3);
    camera.lookAt(0, 0, 0);

    // Load textures
    const textureLoader = new THREE.TextureLoader();
    const tex1 = textureLoader.load('/assets/dashboard-analytics.jpg');
    const tex2 = textureLoader.load('/assets/neural-pattern.jpg');
    const tex3 = textureLoader.load('/assets/dashboard-security.jpg');

    const isMobile = width < 768;
    const cardCount = isMobile ? 1 : 3;
    const textures = [tex1, tex2, tex3];
    const meshes: THREE.Mesh[] = [];

    for (let i = 0; i < cardCount; i++) {
      const geometry = new THREE.PlaneGeometry(1.05, 0.75);
      const material = new THREE.MeshBasicMaterial({
        map: textures[i],
        transparent: true,
        opacity: 1,
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.rotation.x = Math.PI / 4;
      mesh.rotation.y = -Math.PI / 6;
      mesh.position.y = -0.1 + i * 0.1;
      scene.add(mesh);
      meshes.push(mesh);
    }

    // Easing function for cubic-bezier(0.19, 1, 0.22, 1)
    function easeOutExpo(t: number): number {
      return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
    }

    const animate = () => {
      rafRef.current = requestAnimationFrame(animate);

      const t = progressRef.current;
      const eased = easeOutExpo(t);

      // Camera movement
      const startY = -5;
      const endY = 1.2;
      camera.position.y = startY + (endY - startY) * eased;
      camera.lookAt(0, 0, 0);

      // Card explosion
      for (let i = 0; i < meshes.length; i++) {
        const mesh = meshes[i];
        const scaleZ = 1 + (0.8 * t * (i + 1) / meshes.length);
        mesh.scale.set(1, 1, scaleZ);
        const mat = mesh.material as THREE.MeshBasicMaterial;
        mat.opacity = 1 - (t * 0.2);
      }

      renderer.render(scene, camera);
    };
    animate();

    // Scroll handler
    const parent = container.parentElement;
    const handleScroll = () => {
      if (!parent) return;
      const rect = parent.getBoundingClientRect();
      const parentHeight = parent.offsetHeight;
      const viewportH = window.innerHeight;
      const scrolled = -rect.top;
      const totalScroll = parentHeight - viewportH;
      progressRef.current = Math.max(0, Math.min(1, scrolled / totalScroll));
    };
    window.addEventListener('scroll', handleScroll, { passive: true });

    const handleResize = () => {
      const w = container.offsetWidth || window.innerWidth;
      const h = container.offsetHeight || window.innerHeight;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleResize);
      meshes.forEach(m => {
        m.geometry.dispose();
        (m.material as THREE.MeshBasicMaterial).dispose();
      });
      tex1.dispose();
      tex2.dispose();
      tex3.dispose();
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
