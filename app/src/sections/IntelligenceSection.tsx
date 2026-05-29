import NeuralCircuitSystem from '@/effects/NeuralCircuitSystem';
import ScrollRevealText from '@/components/ScrollRevealText';

export default function IntelligenceSection() {
  return (
    <section
      id="enterprise"
      className="relative w-full overflow-hidden bg-black"
      style={{ height: '100vh' }}
    >
      <NeuralCircuitSystem />

      <div className="relative z-10 flex flex-col items-center justify-center h-full px-6">
        <ScrollRevealText className="text-center max-w-2xl">
          <h2
            className="font-display text-white mb-5"
            style={{
              fontSize: 'clamp(28px, 3.5vw, 38px)',
              fontWeight: 500,
              letterSpacing: '-0.01em',
              lineHeight: 1.2,
            }}
          >
            Adaptive Architecture.
          </h2>
          <p
            className="text-white/60"
            style={{
              fontFamily: 'Inter, sans-serif',
              fontSize: '15px',
              lineHeight: 1.6,
            }}
          >
            Our model-agnostic RAG pipeline adapts to your enterprise. Integrating seamlessly
            with your existing infrastructure, security policies, and compliance requirements.
          </p>
        </ScrollRevealText>
      </div>
    </section>
  );
}
