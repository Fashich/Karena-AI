import { useRef, useCallback } from 'react';
import { Link } from 'react-router';
import gsap from 'gsap';

const NAV_LINKS = ['Platform', 'Intelligence', 'Enterprise', 'Security', 'Compliance'];

type NavigationProps = {
  variant?: 'landing' | 'default';
};

export default function Navigation({ variant = 'default' }: NavigationProps) {
  const navRef = useRef<HTMLElement>(null);

  const scrollToSection = useCallback((id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  const handleLinkHover = useCallback((e: React.MouseEvent<HTMLAnchorElement>, entering: boolean) => {
    gsap.to(e.currentTarget, {
      opacity: entering ? 0.6 : 1,
      duration: 0.2,
    });
  }, []);

  return (
    <nav
      ref={navRef}
      className="fixed top-0 left-0 w-full z-50 px-6 py-5 flex items-center justify-between"
    >
      <div className="font-display text-white text-lg font-medium tracking-tight">
        KARENA AI
      </div>

      <div className="hidden md:flex items-center gap-8">
        {NAV_LINKS.map((link) => (
          <a
            key={link}
            href={`#${link.toLowerCase()}`}
            onClick={(e) => {
              e.preventDefault();
              scrollToSection(link.toLowerCase());
            }}
            onMouseEnter={(e) => handleLinkHover(e, true)}
            onMouseLeave={(e) => handleLinkHover(e, false)}
            className="text-white text-xs uppercase tracking-widest cursor-pointer"
            style={{ fontFamily: 'Inter, sans-serif', letterSpacing: '0.02em' }}
          >
            {link}
          </a>
        ))}
      </div>

      <div className="flex items-center gap-3">
        {variant === 'landing' && (
          <Link
            to="/dashboard"
            className="glass-pill text-white text-xs uppercase tracking-widest hover:bg-white/15 transition-colors"
          >
            Dashboard
          </Link>
        )}
        {variant === 'landing' && (
          <Link
            to="/chat"
            className="glass-pill text-white text-xs uppercase tracking-widest hover:bg-white/15 transition-colors"
          >
            Launch Assistant
          </Link>
        )}
        <button
          className="glass-pill text-white text-xs uppercase tracking-widest cursor-pointer hover:bg-white/15 transition-colors"
          onClick={() => scrollToSection('enterprise')}
        >
          Request Demo
        </button>
      </div>
    </nav>
  );
}
