import { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import FluidEngineBackground from '@/effects/FluidEngineBackground';
import MagneticButton from '@/components/MagneticButton';

export default function HeroSection() {
  const navigate = useNavigate();
  const sectionRef = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsVisible(entry.isIntersecting);
      },
      { threshold: 0.1 }
    );

    observer.observe(section);
    return () => observer.disconnect();
  }, []);

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section
      ref={sectionRef}
      id="platform"
      className="relative w-full overflow-hidden"
      style={{ height: '100vh' }}
    >
      <FluidEngineBackground isVisible={isVisible} />

      <div
        className="relative z-10 flex flex-col justify-end h-full px-6 md:px-12 lg:px-20"
        style={{ paddingBottom: '6rem' }}
      >
        <div className="max-w-3xl" style={{ pointerEvents: 'none' }}>
          <h1
            className="font-display text-white mb-5"
            style={{
              fontSize: 'clamp(36px, 5vw, 60px)',
              fontWeight: 500,
              letterSpacing: '-0.02em',
              lineHeight: 1.1,
              textShadow: '0 2px 20px rgba(0,0,0,0.5)',
            }}
          >
            Secure, Real-Time Intelligence.
          </h1>
          <p
            className="text-white/80 mb-8 max-w-xl"
            style={{
              fontFamily: 'Inter, sans-serif',
              fontSize: '15px',
              lineHeight: 1.6,
              textShadow: '0 1px 10px rgba(0,0,0,0.5)',
            }}
          >
            Karena AI transforms fragmented enterprise data into a unified knowledge layer.
            Search, retrieve, and reason with absolute confidence.
          </p>
          <div className="flex gap-4" style={{ pointerEvents: 'auto' }}>
            <MagneticButton
              variant="solid"
              onClick={() => navigate('/chat')}
            >
              Launch Assistant
            </MagneticButton>
            <MagneticButton
              variant="outline"
              onClick={() => scrollToSection('intelligence')}
            >
              View Architecture
            </MagneticButton>
          </div>
        </div>
      </div>
    </section>
  );
}
