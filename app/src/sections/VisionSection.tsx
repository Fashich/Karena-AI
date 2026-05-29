import OrbitMarquee from '@/components/OrbitMarquee';

export default function VisionSection() {
  return (
    <section
      className="relative w-full bg-black flex items-center justify-center overflow-hidden"
      style={{ height: '40vh' }}
    >
      <OrbitMarquee />
    </section>
  );
}
