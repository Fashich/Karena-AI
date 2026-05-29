import { useState } from 'react';

const FOOTER_LINKS = [
  { title: 'Product', items: ['Platform', 'Intelligence', 'Enterprise', 'Pricing'] },
  { title: 'Company', items: ['About', 'Careers', 'Blog', 'Press'] },
  { title: 'Resources', items: ['Documentation', 'API Reference', 'Status', 'Changelog'] },
  { title: 'Legal', items: ['Privacy', 'Terms', 'Security', 'Compliance'] },
];

export default function Footer() {
  const [email, setEmail] = useState('');

  return (
    <footer
      id="compliance"
      className="relative w-full bg-white"
      style={{ minHeight: '60vh', paddingTop: '80px', paddingBottom: '60px' }}
    >
      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-20">
        {/* Top section */}
        <div className="flex flex-col lg:flex-row justify-between gap-12 mb-16">
          {/* Brand */}
          <div className="max-w-sm">
            <h2
              className="font-display text-black mb-4"
              style={{
                fontSize: 'clamp(32px, 4vw, 48px)',
                fontWeight: 500,
                letterSpacing: '-0.02em',
                lineHeight: 1.1,
              }}
            >
              KARENA AI
            </h2>
            <p
              className="text-black/60 mb-6"
              style={{
                fontFamily: 'Inter, sans-serif',
                fontSize: '14px',
                lineHeight: 1.6,
              }}
            >
              Enterprise-grade RAG knowledge intelligence for the world's most demanding organizations.
            </p>

            {/* Newsletter */}
            <div className="flex gap-2">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                className="flex-1 px-4 py-2 text-sm bg-black/5 border border-black/10 rounded text-black placeholder:text-black/40 focus:outline-none focus:border-black/30"
              />
              <button className="px-4 py-2 text-sm bg-black text-white rounded hover:bg-black/80 transition-colors cursor-pointer">
                Subscribe
              </button>
            </div>
          </div>

          {/* Links */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 lg:gap-12">
            {FOOTER_LINKS.map((group) => (
              <div key={group.title}>
                <h4
                  className="font-display text-black text-sm font-medium mb-4 uppercase tracking-wider"
                >
                  {group.title}
                </h4>
                <ul className="space-y-2">
                  {group.items.map((item) => (
                    <li key={item}>
                      <a
                        href="#"
                        className="text-black/50 text-sm hover:text-black transition-colors"
                        style={{ fontFamily: 'Inter, sans-serif' }}
                        onClick={(e) => e.preventDefault()}
                      >
                        {item}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-black/10 pt-6 flex flex-col md:flex-row justify-between items-center gap-4">
          <p
            className="text-black/40 text-xs"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            &copy; {new Date().getFullYear()} Karena AI. All rights reserved.
          </p>
          <div className="flex gap-6">
            {['Twitter', 'LinkedIn', 'GitHub'].map((social) => (
              <a
                key={social}
                href="#"
                className="text-black/40 text-xs hover:text-black transition-colors"
                style={{ fontFamily: 'Inter, sans-serif' }}
                onClick={(e) => e.preventDefault()}
              >
                {social}
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
