import IsometricPlatformStage from '@/effects/IsometricPlatformStage';
import ScrollRevealText from '@/components/ScrollRevealText';

export default function PlatformShowcase() {
  return (
    <section
      id="intelligence"
      className="relative bg-black"
      style={{ minHeight: '200vh' }}
    >
      {/* Sticky container */}
      <div className="sticky top-0 w-full" style={{ height: '100vh' }}>
        <IsometricPlatformStage />

        {/* Overlay text */}
        <div
          className="absolute inset-0 z-10 flex flex-col items-center justify-center pointer-events-none"
        >
          <ScrollRevealText className="text-center px-6">
            <h2
              className="font-display text-white mb-4"
              style={{
                fontSize: 'clamp(28px, 3.5vw, 38px)',
                fontWeight: 500,
                letterSpacing: '-0.01em',
                lineHeight: 1.2,
                textShadow: '0 2px 20px rgba(0,0,0,0.8)',
              }}
            >
              Platform Showcase
            </h2>
            <p
              className="text-white/60 max-w-lg mx-auto"
              style={{
                fontFamily: 'Inter, sans-serif',
                fontSize: '15px',
                lineHeight: 1.6,
                textShadow: '0 1px 10px rgba(0,0,0,0.8)',
              }}
            >
              Explore the unified interface that powers enterprise-grade retrieval, 
              real-time analytics, and seamless knowledge orchestration.
            </p>
          </ScrollRevealText>
        </div>
      </div>
    </section>
  );
}
