import { useRef, useEffect } from 'react';

interface CircuitPoint {
  x: number;
  y: number;
  cp1x: number;
  cp1y: number;
  cp2x: number;
  cp2y: number;
  isBranch?: boolean;
  parentStart?: { x: number; y: number };
}

interface Pulse {
  progress: number;
  speed: number;
}

interface CircuitPath {
  points: CircuitPoint[];
  pulses: Pulse[];
  nextSpawn: number;
}

function createCircuitPath(i: number, total: number, width: number, height: number): CircuitPoint[] {
  const startX = (width / (total + 1)) * (i + 1);
  const points: CircuitPoint[] = [];

  const p0: CircuitPoint = {
    x: startX,
    y: -50,
    cp1x: startX + (Math.random() - 0.5) * 300,
    cp1y: height * 0.25,
    cp2x: startX + (Math.random() - 0.5) * 300,
    cp2y: height * 0.75,
  };
  points.push(p0);

  for (let s = 1; s <= 3; s++) {
    const prev = points[s - 1];
    const branch = Math.random() > 0.7;
    const offsetX = (Math.random() - 0.5) * 150;
    const offsetY = (Math.random() - 0.5) * 150;
    const isEnd = s === 3;

    const newPoint: CircuitPoint = {
      x: isEnd ? startX + offsetX : prev.cp2x + offsetX,
      y: isEnd ? height + 50 : (height * 0.25 * s) + offsetY,
      cp1x: 0,
      cp1y: 0,
      cp2x: 0,
      cp2y: 0,
      isBranch: false,
    };

    if (branch && !isEnd) {
      const parentX = prev.x;
      const parentY = prev.y;
      const branchX = prev.cp2x + offsetX + 200;
      const branchY = (height * 0.25 * s) + offsetY - 150;
      points.push({
        x: branchX,
        y: branchY,
        cp1x: parentX,
        cp1y: parentY,
        cp2x: branchX,
        cp2y: branchY,
        isBranch: true,
        parentStart: { x: parentX, y: parentY },
      });
      newPoint.cp1x = parentX;
      newPoint.cp1y = parentY;
    } else {
      newPoint.cp1x = prev.cp2x;
      newPoint.cp1y = prev.cp2y;
    }

    newPoint.cp2x = isEnd ? startX + offsetX : prev.cp2x + (Math.random() - 0.5) * 300;
    newPoint.cp2y = isEnd ? height * 0.75 : (height * 0.25 * s) + offsetY;

    points.push(newPoint);
  }

  return points;
}

export default function NeuralCircuitSystem() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = window.innerWidth;
    const height = window.innerHeight;
    const dpr = Math.min(window.devicePixelRatio, 2);
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    const isMobile = width < 768;
    const numPaths = isMobile ? 4 : 8;
    const paths: CircuitPath[] = [];

    for (let i = 0; i < numPaths; i++) {
      const pts = createCircuitPath(i, numPaths, width, height);
      paths.push({
        points: pts,
        pulses: [],
        nextSpawn: Math.random() * 1000,
      });
    }

    function drawPath(ctx: CanvasRenderingContext2D, points: CircuitPoint[]) {
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i++) {
        const p = points[i];
        if (p.isBranch && p.parentStart) {
          ctx.moveTo(p.parentStart.x, p.parentStart.y);
        }
        ctx.bezierCurveTo(p.cp1x, p.cp1y, p.cp2x, p.cp2y, p.x, p.y);
      }
      ctx.strokeStyle = 'rgba(255,255,255,0.05)';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Gradient glow overlay
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i++) {
        const p = points[i];
        if (p.isBranch && p.parentStart) {
          ctx.moveTo(p.parentStart.x, p.parentStart.y);
        }
        ctx.bezierCurveTo(p.cp1x, p.cp1y, p.cp2x, p.cp2y, p.x, p.y);
      }
      const grad = ctx.createLinearGradient(
        points[0].x, points[0].y,
        points[points.length - 1].x, points[points.length - 1].y
      );
      grad.addColorStop(0, 'rgba(255,255,255,0)');
      grad.addColorStop(0.3, 'rgba(103, 52, 255, 0.1)');
      grad.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.strokeStyle = grad;
      ctx.lineWidth = 4;
      ctx.stroke();
    }

    function drawPulse(ctx: CanvasRenderingContext2D, points: CircuitPoint[], progress: number) {
      const totalSegments = points.length - 1;
      const seg = progress * totalSegments;
      const idx = Math.floor(seg);
      const t = seg - idx;
      if (idx >= totalSegments) return;

      const p0 = points[idx];
      const p1 = points[idx + 1];

      const t2 = t * t;
      const t3 = t2 * t;
      const u = 1.0 - t;
      const u2 = u * u;
      const u3 = u2 * u;

      const x = u3 * p0.x + 3.0 * u2 * t * p0.cp1x + 3.0 * u * t2 * p0.cp2x + t3 * p1.x;
      const y = u3 * p0.y + 3.0 * u2 * t * p0.cp1y + 3.0 * u * t2 * p0.cp2y + t3 * p1.y;

      const grad = ctx.createRadialGradient(x, y, 0, x, y, 12);
      grad.addColorStop(0, 'rgba(255,255,255,1)');
      grad.addColorStop(0.4, 'rgba(103, 52, 255, 0.8)');
      grad.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(x, y, 12, 0, Math.PI * 2);
      ctx.fill();
    }

    const animate = () => {
      rafRef.current = requestAnimationFrame(animate);

      // Fade trail effect
      ctx.fillStyle = 'rgba(0,0,0,0.1)';
      ctx.fillRect(0, 0, width, height);

      const now = performance.now();

      for (const path of paths) {
        // Draw the path
        drawPath(ctx, path.points);

        // Spawn new pulses
        if (now > path.nextSpawn) {
          path.pulses.push({
            progress: 0,
            speed: 0.002 + Math.random() * 0.003,
          });
          path.nextSpawn = now + 300 + Math.random() * 1200;
        }

        // Update and draw pulses
        for (let i = path.pulses.length - 1; i >= 0; i--) {
          const pulse = path.pulses[i];
          pulse.progress += pulse.speed;
          if (pulse.progress >= 1) {
            path.pulses.splice(i, 1);
            continue;
          }
          drawPulse(ctx, path.points, pulse.progress);
        }
      }
    };

    animate();

    const handleResize = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
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
