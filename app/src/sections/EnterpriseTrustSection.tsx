import { useRef, useEffect } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import HolographicMeshGrid from '@/effects/HolographicMeshGrid';

gsap.registerPlugin(ScrollTrigger);

const FEATURES = [
  { label: '99.9% Uptime', sub: 'Enterprise SLA Guaranteed' },
  { label: 'SOC 2 Compliance', sub: 'Type II Certified' },
  { label: 'Real-time Monitoring', sub: 'Sub-1s Response Time' },
  { label: 'End-to-End Encryption', sub: 'AES-256 at Rest' },
  { label: 'GDPR & CCPA Ready', sub: 'Global Privacy Standards' },
];

export default function EnterpriseTrustSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const itemsRef = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    if (!sectionRef.current) return;

    const ctx = gsap.context(() => {
      itemsRef.current.forEach((item) => {
        if (!item) return;
        gsap.fromTo(
          item,
          { opacity: 0, y: 40 },
          {
            opacity: 1,
            y: 0,
            duration: 0.6,
            ease: 'power2.out',
            scrollTrigger: {
              trigger: item,
              start: 'top 85%',
              toggleActions: 'play none none reverse',
            },
          }
        );
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section
      id="security"
      ref={sectionRef}
      className="relative bg-black"
      style={{ minHeight: '300vh' }}
    >
      <HolographicMeshGrid />

      {/* Scrolling text overlays */}
      <div
        className="relative z-10 w-full"
        style={{ marginTop: '-100vh', paddingTop: '100vh' }}
      >
        {FEATURES.map((feature, i) => (
          <div
            key={i}
            ref={(el) => { itemsRef.current[i] = el; }}
            className="flex flex-col items-center justify-center px-6"
            style={{
              minHeight: '60vh',
              paddingTop: '10vh',
              paddingBottom: '10vh',
            }}
          >
            <div className="glass-card px-8 py-6 text-center max-w-md">
              <h3
                className="font-display text-white mb-2"
                style={{
                  fontSize: 'clamp(20px, 2.5vw, 28px)',
                  fontWeight: 500,
                  letterSpacing: '-0.01em',
                }}
              >
                {feature.label}
              </h3>
              <p
                className="text-white/50"
                style={{
                  fontFamily: 'Inter, sans-serif',
                  fontSize: '13px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.02em',
                }}
              >
                {feature.sub}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
