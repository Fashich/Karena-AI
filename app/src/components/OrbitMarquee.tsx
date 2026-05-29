import { useMemo } from 'react';

const TEXT = "KARENA AI \u2014 INTELLIGENCE FORWARD \u2014 ";

const ROWS = [
  { translateZ: 50, rotateX: 0, rotateY: 0, scaleX: 1, scaleY: 1, delay: -20 },
  { translateZ: -20, rotateX: -15, rotateY: 10, scaleX: -1, scaleY: 1, delay: -18 },
  { translateZ: 100, rotateX: 0, rotateY: 0, scaleX: 1, scaleY: 1, delay: -16, scale: 1.5 },
  { translateZ: -100, rotateX: 20, rotateY: 0, scaleX: 1, scaleY: -1, delay: -14, rotateZ: 10 },
];

export default function OrbitMarquee() {
  const words = useMemo(() => TEXT.split(' '), []);

  return (
    <div
      style={{
        perspective: '600px',
        width: '100%',
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {ROWS.map((row, rowIdx) => (
        <div
          key={rowIdx}
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            transform: `translateZ(${row.translateZ}px) rotateX(${row.rotateX}deg) rotateY(${row.rotateY}deg) rotateZ(${row.rotateZ || 0}deg) scaleX(${row.scaleX}) scaleY(${row.scaleY}) scale(${row.scale || 1})`,
            transformStyle: 'preserve-3d',
          }}
        >
          <div
            className="flex items-center whitespace-nowrap"
            style={{
              animation: `marqueeSlide 30s linear infinite`,
              animationDelay: `${row.delay}s`,
            }}
          >
            {[...words, ...words, ...words, ...words].map((word, i) => (
              <span
                key={i}
                className="font-display text-white/60 mx-2"
                style={{
                  fontSize: 'clamp(24px, 4vw, 48px)',
                  fontWeight: 500,
                  letterSpacing: '-0.02em',
                  textTransform: 'uppercase',
                }}
              >
                {word}
              </span>
            ))}
          </div>
        </div>
      ))}

      <style>{`
        @keyframes marqueeSlide {
          0% { transform: translateX(0%); }
          100% { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}
