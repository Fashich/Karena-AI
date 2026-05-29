import { useRef, useCallback } from 'react';
import gsap from 'gsap';

interface MagneticButtonProps {
  children: React.ReactNode;
  variant?: 'solid' | 'outline';
  onClick?: () => void;
  className?: string;
}

export default function MagneticButton({
  children,
  variant = 'solid',
  onClick,
  className = '',
}: MagneticButtonProps) {
  const btnRef = useRef<HTMLButtonElement>(null);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!btnRef.current) return;
    const rect = btnRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    gsap.to(btnRef.current, {
      x: x * 0.3,
      y: y * 0.3,
      duration: 0.3,
      ease: 'power2.out',
    });
  }, []);

  const handleMouseLeave = useCallback(() => {
    if (!btnRef.current) return;
    gsap.to(btnRef.current, {
      x: 0,
      y: 0,
      duration: 0.5,
      ease: 'elastic.out(1, 0.3)',
    });
  }, []);

  const baseClasses =
    'relative inline-flex items-center justify-center px-6 py-3 text-sm font-medium tracking-wide uppercase transition-colors duration-200 cursor-pointer';
  const solidClasses = 'bg-white text-black hover:bg-white/90';
  const outlineClasses =
    'bg-transparent text-white border border-white/30 hover:border-white/60 hover:bg-white/5';

  return (
    <button
      ref={btnRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      className={`${baseClasses} ${
        variant === 'solid' ? solidClasses : outlineClasses
      } ${className}`}
      style={{ borderRadius: '4px' }}
    >
      {children}
    </button>
  );
}
