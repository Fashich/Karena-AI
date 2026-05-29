import { useEffect, useRef } from 'react';
import Lenis from '@studio-freight/lenis';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

import Navigation from '@/sections/Navigation';
import HeroSection from '@/sections/HeroSection';
import VisionSection from '@/sections/VisionSection';
import PlatformShowcase from '@/sections/PlatformShowcase';
import IntelligenceSection from '@/sections/IntelligenceSection';
import EnterpriseTrustSection from '@/sections/EnterpriseTrustSection';
import Footer from '@/sections/Footer';

gsap.registerPlugin(ScrollTrigger);

export default function Landing() {
  const lenisRef = useRef<Lenis | null>(null);

  useEffect(() => {
    const lenis = new Lenis({ lerp: 0.1, smoothWheel: true });
    lenisRef.current = lenis;
    lenis.on('scroll', ScrollTrigger.update);
    gsap.ticker.add((time) => {
      lenis.raf(time * 1000);
    });
    gsap.ticker.lagSmoothing(0);
    return () => {
      lenis.destroy();
    };
  }, []);

  return (
    <div className="relative">
      <Navigation variant="landing" />
      <main>
        <HeroSection />
        <VisionSection />
        <PlatformShowcase />
        <IntelligenceSection />
        <EnterpriseTrustSection />
      </main>
      <Footer />
    </div>
  );
}
