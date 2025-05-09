import type { ReactNode } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useState } from 'react';
import { Dialog } from '@headlessui/react';

const menuItems = [
  { text: 'Home', path: '/' },
  { text: 'Clubs', path: '/clubs' },
  { text: 'Competitions', path: '/competitions' },
  { text: 'Fixtures', path: '/fixtures' },
  { text: 'Predictions', path: '/predictions' },
];

interface LayoutProps {
  children: ReactNode;
}

function Logo() {
  // Simple SVG football logo
  return (
    <span className="flex items-center gap-2 select-none">
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="14" cy="14" r="13" fill="#2563eb" stroke="#1e40af" strokeWidth="2" />
        <polygon points="14,7 18,11 16,17 12,17 10,11" fill="#fff" stroke="#1e40af" strokeWidth="1.2" />
      </svg>
      <span className="font-extrabold text-xl tracking-tight text-primary">Match<span className="text-accent">Wise</span></span>
    </span>
  );
}

function UserAvatar() {
  // Placeholder avatar
  return (
    <div className="ml-6 flex items-center gap-2 cursor-pointer group">
      <img src="https://ui-avatars.com/api/?name=User&background=2563eb&color=fff&rounded=true&size=32" alt="User" className="w-8 h-8 rounded-full border-2 border-primary/30 group-hover:border-primary transition" />
      <span className="hidden md:inline text-sm font-semibold text-text-secondary group-hover:text-primary transition">Profile</span>
    </div>
  );
}

export default function Layout({ children }: LayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="min-h-screen w-screen bg-gradient-to-br from-background-DEFAULT to-background-soft overflow-x-hidden font-sans">
      {/* Top Navbar */}
      <nav className="sticky top-0 left-0 right-0 h-16 bg-white/95 border-b border-slate-200 flex items-center px-6 z-30 w-full shadow-sm backdrop-blur-md">
        {/* Logo */}
        <button className="flex items-center gap-2 mr-10 focus:outline-none" onClick={() => navigate('/')} aria-label="Go to home">
          <Logo />
        </button>
        <div className="hidden md:flex gap-1 flex-1">
          {menuItems.map((item) => (
            <button
              key={item.text}
              className={`relative px-5 py-2 rounded-full font-semibold transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-primary/30
                ${location.pathname === item.path
                  ? 'bg-primary/10 text-primary shadow-sm after:absolute after:left-1/2 after:-bottom-1 after:-translate-x-1/2 after:w-2/3 after:h-1 after:rounded-full after:bg-primary after:content-[""]'
                  : 'text-text-secondary hover:bg-primary/5 hover:text-primary'}`}
              onClick={() => navigate(item.path)}
            >
              {item.text}
            </button>
          ))}
        </div>
        {/* User Avatar/Profile */}
        <UserAvatar />
        {/* Mobile Hamburger */}
        <button
          className="md:hidden ml-auto p-2 rounded hover:bg-slate-100 focus:outline-none"
          onClick={() => setMobileOpen(true)}
          aria-label="Open menu"
        >
          <span className="inline-block w-6 h-6">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </span>
        </button>
      </nav>
      {/* Mobile Nav Drawer */}
      <Dialog open={mobileOpen} onClose={() => setMobileOpen(false)} className="relative z-40 md:hidden">
        <div className="fixed inset-0 bg-black/30" aria-hidden="true" />
        <div className="fixed top-0 left-0 w-64 h-full bg-white shadow-lg flex flex-col">
          <div className="h-16 flex items-center px-4 font-bold text-xl border-b border-gray-200">
            <Logo />
            <button
              className="ml-auto p-2 rounded hover:bg-gray-100"
              onClick={() => setMobileOpen(false)}
              aria-label="Close menu"
            >
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <nav className="flex-1 py-4">
            <ul className="space-y-2">
              {menuItems.map((item) => (
                <li key={item.text}>
                  <button
                    className={`w-full text-left px-6 py-2 rounded-lg font-semibold transition-colors hover:bg-primary/10 hover:text-primary focus:outline-none focus:ring-2 focus:ring-primary/30 ${location.pathname === item.path ? 'bg-primary text-white shadow' : 'text-text-secondary'}`}
                    onClick={() => {
                      navigate(item.path);
                      setMobileOpen(false);
                    }}
                  >
                    {item.text}
                  </button>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </Dialog>
      {/* Main content below navbar */}
      <main className="pt-16 w-full min-h-screen">
        {children}
      </main>
    </div>
  );
} 