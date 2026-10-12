import { useState, useEffect } from 'react';
import { Menu, X, ArrowRight } from 'lucide-react';

const GET_STARTED_HREF = 'mailto:vajra.techworks@gmail.com?subject=VAJRA%20First%20Partner%20Enquiry';

export default function VajraNavbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 40);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const closeMobileMenu = () => setMobileMenuOpen(false);

  return (
    <>
      <header className={`vajra-floating-navbar ${isScrolled ? 'is-scrolled' : ''}`}>
        <div className="navbar-glass-container">
          {/* Original VAJRA Logo */}
          <a href="#hero" className="navbar-logo-link" onClick={closeMobileMenu}>
            <img
              src="/vajra-logo.png"
              alt="VAJRA"
              className="navbar-brand-logo"
              draggable="false"
            />
          </a>

          {/* Desktop Navigation Links */}
          <nav className="navbar-desktop-nav" aria-label="Main Navigation">
            <a href="#journey" className="nav-item-link">How It Works</a>
            <a href="#services" className="nav-item-link">Services</a>
            <a href="#pricing" className="nav-item-link">Pricing</a>
          </nav>

          {/* Action CTA */}
          <div className="navbar-action-cluster">
            <a href={GET_STARTED_HREF} className="vajra-nav-cta-btn">
              <span>GET STARTED</span>
              <ArrowRight size={15} />
            </a>

            {/* Mobile Hamburger toggle */}
            <button
              type="button"
              className="navbar-mobile-toggle"
              aria-label={mobileMenuOpen ? 'Close Menu' : 'Open Menu'}
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>
      </header>

      {/* Full-Screen Mobile Glass Drawer */}
      {mobileMenuOpen && (
        <div className="vajra-mobile-menu-overlay" role="dialog" aria-modal="true">
          <div className="mobile-menu-glass-panel">
            <div className="mobile-menu-header">
              <img src="/vajra-logo.png" alt="VAJRA" className="mobile-menu-logo" />
              <button
                type="button"
                className="mobile-close-btn"
                onClick={closeMobileMenu}
                aria-label="Close Navigation"
              >
                <X size={24} />
              </button>
            </div>

            <nav className="mobile-nav-links">
              <a href="#journey" onClick={closeMobileMenu} className="mobile-link">
                How It Works
              </a>
              <a href="#services" onClick={closeMobileMenu} className="mobile-link">
                Services
              </a>
              <a href="#pricing" onClick={closeMobileMenu} className="mobile-link">
                Pricing
              </a>
            </nav>

            <div className="mobile-menu-footer">
              <a
                href={GET_STARTED_HREF}
                onClick={closeMobileMenu}
                className="vajra-btn-primary vajra-btn-full"
              >
                <span>GET STARTED</span>
                <ArrowRight size={18} />
              </a>
              <a className="mobile-menu-email" href="mailto:vajra.techworks@gmail.com">vajra.techworks@gmail.com</a>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
