import { useRef, useEffect } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

interface ScrollRevealTextProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}

export default function ScrollRevealText({
  children,
  className = '',
  delay = 0,
}: ScrollRevealTextProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;

    const ctx = gsap.context(() => {
      gsap.from(ref.current!, {
        y: 30,
        opacity: 0,
        duration: 0.8,
        delay,
        ease: 'power2.out',
        scrollTrigger: {
          trigger: ref.current!,
          start: 'top 80%',
          toggleActions: 'play none none reverse',
        },
      });
    });

    return () => ctx.revert();
  }, [delay]);

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}
