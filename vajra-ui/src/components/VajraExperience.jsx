import { useEffect, useState } from 'react';
import {
  Sparkles,
  CheckCircle2,
  ShieldCheck,
  ArrowRight,
  ChevronRight,
  Store,
  TrendingUp,
} from 'lucide-react';

const GET_STARTED_HREF = 'mailto:vajra.techworks@gmail.com?subject=VAJRA%20First%20Partner%20Enquiry';
const CONTACT_EMAIL = 'vajra.techworks@gmail.com';

export default function VajraExperience() {
  const [activeService, setActiveService] = useState(0);
  const [activeJourneyStep, setActiveJourneyStep] = useState(0);

  useEffect(() => {
    const sections = [
      { selector: '.journey-step-item', update: setActiveJourneyStep },
      { selector: '.service-story-panel', update: setActiveService },
    ];
    const observers = sections.map(({ selector, update }) => {
      const nodes = document.querySelectorAll(selector);
      if (!('IntersectionObserver' in window)) return null;
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) update(Number(entry.target.dataset.storyIndex));
        });
      }, { rootMargin: '-38% 0px -42% 0px', threshold: 0 });
      nodes.forEach((node) => observer.observe(node));
      return observer;
    });
    return () => observers.forEach((observer) => observer?.disconnect());
  }, []);

  const journeySteps = [
    {
      id: 'connect', number: '01', title: 'Customer connects', tagline: 'At the table',
      description: 'A table standee gives each guest a simple place to begin.',
      visual: (<div className="journey-visual-orbit"><div className="journey-orbit-ring" /><div className="journey-feedback-object"><img src="/vajra-symbol.png" alt="" /><span>A thoughtful visit starts here.</span><span className="journey-object-caption">VAJRA for cafés & restaurants</span></div><span className="journey-float-label label-one">Tap to begin</span><span className="journey-float-label label-two">No app needed</span></div>),
    },
    {
      id: 'share', number: '02', title: 'Shares an experience', tagline: 'A few simple taps',
      description: 'Guests share what stood out across food, service and ambience.',
      visual: (<div className="journey-visual-orbit"><div className="journey-orbit-ring" /><div className="journey-feedback-object"><span>How was your visit?</span><div className="journey-choice-row"><span>Food</span><span>Service</span><span>Ambience</span></div><div className="journey-choice-glow" /></div><span className="journey-float-label label-one">Customer feedback</span><span className="journey-float-label label-two">In their own words</span></div>),
    },
    {
      id: 'assist', number: '03', title: 'Gets review assistance', tagline: 'True to their experience',
      description: 'Their real feedback becomes a natural draft they can shape and edit.',
      visual: (<div className="journey-visual-orbit draft-orbit"><div className="journey-orbit-ring" /><div className="journey-draft-object"><span className="journey-object-kicker">A REVIEW, IN THEIR WORDS</span><div className="draft-line long" /><div className="draft-line" /><div className="draft-line short" /><div className="draft-object-footer"><span>Review draft</span><span>Optional · editable</span></div></div><span className="journey-float-label label-one">Built from their feedback</span><span className="journey-float-label label-two">Ready to edit</span></div>),
    },
    {
      id: 'google', number: '04', title: 'Continues to Google', tagline: 'One clear next step',
      description: 'Guests can continue to the restaurant’s Google review page.',
      visual: (<div className="journey-visual-orbit google-orbit"><div className="journey-orbit-ring" /><div className="journey-google-object"><span className="google-g-mark">G</span><span>Continue to Google</span><ArrowRight size={20} /></div><span className="journey-float-label label-one">Customer chooses</span><span className="journey-float-label label-two">Restaurant review page</span></div>),
    },
    {
      id: 'feedback', number: '05', title: 'Understands customer feedback', tagline: 'For the restaurant',
      description: 'Customer feedback and activity become easier for the restaurant to see.',
      visual: (<div className="journey-visual-orbit insight-orbit"><div className="journey-orbit-ring" /><div className="journey-signal-object"><img src="/vajra-symbol.png" alt="" /><span className="signal-node node-a">Customer feedback</span><span className="signal-node node-b">Guest activity</span><span className="signal-node node-c">For your restaurant</span><i className="signal-pulse pulse-a" /><i className="signal-pulse pulse-b" /></div><span className="journey-float-label label-one">Owner Insights</span><span className="journey-float-label label-two">A clearer picture</span></div>),
    },
  ];

  const services = [
    { num: '01', title: 'Customer Feedback', quote: 'Give customers a simple way to share their experience.' },
    { num: '02', title: 'AI Review Assistance', quote: 'Help customers turn their real experience into a natural review draft.' },
    { num: '03', title: 'Google Review Journey', quote: 'Make it easy for customers to continue to your Google review page.' },
    { num: '04', title: 'Owner Insights', quote: 'See activity and customer feedback from your restaurant.' },
  ];

  return (
    <div className="vajra-narrative-experience">
      {/* ─── SECTION 1: HERO EXPERIENCE ────────────────────────────────────── */}
      <section className="vajra-section vajra-hero-section" id="hero">
        <div className="vajra-container">
          <div className="hero-spatial-grid">
            <div className="hero-content-column">
              <div className="hero-eyebrow-container">
                <span className="hero-eyebrow-symbol">
                  <img src="/vajra-symbol.png" alt="" className="eyebrow-logo-mark" />
                </span>
                <span className="hero-eyebrow-text">
                  CUSTOMER EXPERIENCE FOR CAFÉS & RESTAURANTS
                </span>
              </div>

              <h1 className="hero-massive-headline">
                Make every<br />
                <span className="text-gradient-cyan">customer experience</span><br />
                count.
              </h1>

              <p className="hero-supporting-lead">
                A simple way for café and restaurant guests to share feedback,
                get review assistance, and continue to Google.
              </p>

              <div className="hero-actions-group">
                <a href={GET_STARTED_HREF} className="vajra-btn-primary">
                  <span>GET STARTED</span>
                  <ArrowRight size={18} />
                </a>
                <a href="#journey" className="vajra-btn-glass">
                  <span>EXPLORE VAJRA</span>
                  <ArrowRight size={16} />
                </a>
              </div>
              <a className="hero-plan-note" href="#pricing">₹6,999 / year <span>·</span> 5 standees included</a>
            </div>

            {/* Spatial Hero Floating Glass Construct */}
            <div className="hero-spatial-canvas-column">
              <div className="hero-glass-experience-card">
                <div className="hero-card-glow-mesh" />

                <div className="hero-card-header">
                  <div className="brand-badge-mini">
                    <img src="/vajra-symbol.png" alt="" className="mini-vajra-symbol" />
                    <span>VAJRA CUSTOMER EXPERIENCE</span>
                  </div>
                  <span className="live-status-pill">CAFÉS · RESTAURANTS</span>
                </div>

                <div className="hero-card-interaction-block">
                  <div className="hero-flow-list">
                    <div><span>01</span><strong>Customer feedback</strong><i>Share</i></div>
                    <div><span>02</span><strong>Customer feedback</strong><i>Share</i></div>
                    <div><span>03</span><strong>Review assistance</strong><i>Shape</i></div>
                    <div><span>04</span><strong>Google review page</strong><i>Continue</i></div>
                    <div><span>05</span><strong>Owner insights</strong><i>Understand</i></div>
                  </div>
                  <p className="hero-card-note">From the table to a clearer view of customer feedback.</p>
                </div>

                {/* Floating Clay Accents */}
                <div className="floating-clay-pill clay-pill-1">
                  <span>5 Premium Table Standees</span>
                </div>
                <div className="floating-clay-pill clay-pill-2">
                  <span>QR + NFC technology</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── SECTION 2: VAJRA WORLD & BRAND PHILOSOPHY ─────────────────────── */}
      <section className="vajra-section vajra-world-section" id="world">
        <div className="vajra-container">
          <div className="section-header-centered">
            <span className="neo-section-marker">01 / ARCHITECTURE</span>
            <h2 className="section-headline">
              A simpler customer feedback and review experience
            </h2>
            <p className="section-subheadline">
              VAJRA helps cafés and restaurants make it easier for guests to share their experience and continue to Google.
            </p>
          </div>

          <div className="vajra-world-grid">
            <div className="world-feature-card glass-panel-deep">
              <div className="feature-icon-wrapper">
                <Store size={28} />
              </div>
              <h3 className="feature-card-title">At the Dining Table</h3>
              <p className="feature-card-desc">
                A table standee gives customers a simple place to begin sharing their experience.
              </p>
              
            </div>

            <div className="world-feature-card glass-panel-deep">
              <div className="feature-icon-wrapper">
                <Sparkles size={28} />
              </div>
              <h3 className="feature-card-title">A review in their own words</h3>
              <p className="feature-card-desc">
                Review assistance helps customers turn the details they shared into a natural draft they can edit.
              </p>
              
            </div>

            <div className="world-feature-card glass-panel-deep">
              <div className="feature-icon-wrapper">
                <TrendingUp size={28} />
              </div>
              <h3 className="feature-card-title">Customer feedback</h3>
              <p className="feature-card-desc">
                Owner Insights helps restaurants see customer feedback and activity in one place.
              </p>
              
            </div>
          </div>
        </div>
      </section>

      {/* ─── SECTION 3: THE CUSTOMER JOURNEY (SCROLL-DRIVEN STORY) ──────────── */}
      <section className="vajra-section vajra-journey-section" id="journey">
        <div className="vajra-container">
          <div className="section-header-left">
            <span className="neo-section-marker">02 / CONTINUOUS NARRATIVE</span>
            <h2 className="section-headline">
              From the table to Google, with care
            </h2>
            <p className="section-subheadline">
              Five clear steps that help guests share a real experience and help restaurants understand feedback.
            </p>
          </div>

          <div className="journey-spatial-layout">
            {/* Step navigation / timeline selector */}
            <div className="journey-steps-selector">
              {journeySteps.map((step, index) => (
                <button
                  key={step.id}
                  type="button"
                  data-story-index={index}
                  className={`journey-step-item ${activeJourneyStep === index ? 'active' : ''}`}
                  onClick={() => setActiveJourneyStep(index)}
                >
                  <div className="step-item-meta">
                    <span className="step-number">{step.number}</span>
                    <span className="step-tagline">{step.tagline}</span>
                  </div>
                  <h3 className="step-title">{step.title}</h3>
                  <p className="step-desc">{step.description}</p>
                </button>
              ))}
            </div>

            {/* Spatial live visual representation */}
            <div className="journey-stage-display">
              <div className="journey-glass-display-frame glass-panel-elevated">
                <div className="stage-top-bar">
                  <div className="stage-pill">
                    <span className="pulse-indicator" />
                    <span>PHASE {journeySteps[activeJourneyStep].number} IN MOTION</span>
                  </div>
                  <span className="stage-label">{journeySteps[activeJourneyStep].title}</span>
                </div>
                <div className="stage-body">
                  {journeySteps[activeJourneyStep].visual}
                </div>
                <div className="stage-footer">
                  <div className="stage-progress-indicators">
                    {journeySteps.map((_, i) => (
                      <span
                        key={i}
                        className={`progress-bar-segment ${i === activeJourneyStep ? 'active' : i < activeJourneyStep ? 'completed' : ''}`}
                        onClick={() => setActiveJourneyStep(i)}
                      />
                    ))}
                  </div>
                  <button
                    type="button"
                    className="stage-next-btn"
                    onClick={() => setActiveJourneyStep((prev) => (prev + 1) % journeySteps.length)}
                  >
                    <span>Next Stage</span>
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── SECTION 4: THE FOUR CORE SERVICES ──────────────────────────────── */}
      <section className="vajra-section vajra-services-section" id="services">
        <div className="vajra-container">
          <div className="section-header-centered">
            <span className="neo-section-marker">03 / CORE CAPABILITIES</span>
            <h2 className="section-headline">
              The Four Pillars of VAJRA
            </h2>
            <p className="section-subheadline">
              Four simple parts support the same customer journey.
            </p>
          </div>

          <div className="services-spatial-container">
            <div className="services-story-orbit" aria-hidden="true">
              <div className="services-orbit-ring" />
              <img src="/vajra-symbol.png" alt="" />
              <span>FOUR CONNECTED SERVICES</span>
              <div className="services-orbit-track"><i className={activeService >= 0 ? 'active' : ''} /><i className={activeService >= 1 ? 'active' : ''} /><i className={activeService >= 2 ? 'active' : ''} /><i className={activeService >= 3 ? 'active' : ''} /></div>
            </div>
            <div className="services-story-list">
              {services.map((service, index) => (
                <button
                  className={`service-story-panel glass-panel-deep ${activeService === index ? 'active' : ''}`}
                  key={service.num}
                  type="button"
                  data-story-index={index}
                  onClick={() => setActiveService(index)}
                >
                  <span className="service-story-index">{service.num}<span> / 04</span></span>
                  <ArrowRight size={20} className="service-story-arrow" />
                  <span className="service-story-label">VAJRA SERVICE</span>
                  <strong>{service.title}</strong>
                  <span className="service-story-description">{service.quote}</span>
                </button>
              ))}
              <div className="service-story-actions">
                <a href={GET_STARTED_HREF} className="vajra-btn-primary">
                  <span>GET STARTED</span><ArrowRight size={16} />
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── SECTION 5: WHAT YOU GET ─────────────────────────────────────── */}
      <section className="vajra-section vajra-package-section" id="included">
        <div className="vajra-container">
          <div className="package-story-panel glass-panel-deep">
            <div className="package-story-copy">
              <span className="neo-section-marker">04 / WHAT YOU GET</span>
              <h2 className="section-headline">Everything to get started at your tables.</h2>
              <p className="section-subheadline">One connected customer experience, with the setup and support to keep it running.</p>
            </div>
            <div className="package-includes-list">
              {[
                ['05', 'Premium table standees'],
                ['QR + NFC', 'Ways to connect'],
                ['4 services', 'Feedback through to Owner Insights'],
                ['Included', 'Setup, hosting, maintenance and updates'],
                ['Included', 'Support'],
              ].map(([mark, label]) => (
                <div className="package-includes-item" key={label}>
                  <span>{mark}</span><strong>{label}</strong><ArrowRight size={16} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ─── SECTION 6: FIRST PARTNER OFFER & PRICING ──────────────────────── */}
      <section className="vajra-section vajra-pricing-section" id="pricing">
        <div className="vajra-container">
          <div className="section-header-centered">
            <span className="neo-section-marker">05 / INVESTMENT</span>
            <div className="first-partner-badge">
              <Sparkles size={14} />
              <span>VAJRA FIRST PARTNER PROGRAM</span>
            </div>
            <h2 className="section-headline">
              Simple, Transparent Pricing
            </h2>
            <p className="section-subheadline">
              Special launch pricing for our first partner businesses. A clear annual plan for café and restaurant partners.
            </p>
          </div>

          <div className="pricing-spatial-card-wrapper">
            <div className="pricing-spatial-panel glass-panel-elevated">
              <div className="pricing-panel-top">
                <div className="plan-identity">
                  <div className="plan-name-badge">VAJRA FIRST PARTNER</div>
                  <div className="plan-saving-callout">
                    <span>₹2,000 launch saving against the regular ₹8,999 annual plan</span>
                  </div>
                </div>

                <div className="plan-price-block">
                  <div className="price-currency">₹</div>
                  <div className="price-amount">6,999</div>
                  <div className="price-cycle">/ year</div>
                </div>
              </div>

              <div className="pricing-divider" />

              <div className="pricing-includes-header">
                ALL-INCLUSIVE PARTNER PACKAGE:
              </div>

              <div className="pricing-features-grid">
                {[
                  '5 Premium Table Standees',
                  'QR + NFC Technology',
                  'Customer Feedback',
                  'AI Review Assistance',
                  'Google Review Journey',
                  'Owner Insights',
                  'Setup',
                  'Hosting',
                  'Maintenance',
                  'Updates',
                  'Support',
                ].map((item) => (
                  <div key={item} className="pricing-benefit-item">
                    <CheckCircle2 size={18} className="benefit-check" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>

              <div className="standee-ownership-clarity">
                <div className="standee-clarity-badge">
                  <ShieldCheck size={18} className="text-cyan" />
                  <div>
                    <strong>Physical Standees Stay With Your Business</strong>
                    <p>They do NOT need to be repurchased every year. Only additional or replacement units require payment.</p>
                  </div>
                </div>
                <div className="standee-extra-cost">
                  <span className="extra-tag">Need more tables?</span>
                  <span className="extra-amount">₹299 / standee (one-time)</span>
                </div>
              </div>

              <div className="pricing-action-row">
                <a href={GET_STARTED_HREF} className="vajra-btn-primary vajra-btn-large">
                  <span>GET STARTED</span>
                  <ArrowRight size={20} />
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── SECTION 6: CONTACT ────────────────────────────────────────────── */}
      <section className="vajra-section vajra-cta-section" id="start">
        <div className="vajra-container">
          <div className="final-cta-panel glass-panel-deep">
            <div className="cta-brand-motif">
              <img src="/vajra-symbol.png" alt="" className="cta-symbol-img" />
            </div>
            <span className="neo-section-marker">06 / GET STARTED</span>
            <h2 className="cta-headline">Ready to bring VAJRA to your tables?</h2>
            <p className="cta-description">Let’s set up a better customer experience for your café or restaurant.</p>
            <div className="cta-action-cluster">
              <a href={GET_STARTED_HREF} className="vajra-btn-primary vajra-btn-large">
                <span>GET STARTED</span><ArrowRight size={20} />
              </a>
            </div>
            <a className="contact-email-link" href="mailto:vajra.techworks@gmail.com">{CONTACT_EMAIL}</a>
          </div>
        </div>
      </section>

      {/* ─── FOOTER ────────────────────────────────────────────────────────── */}
      <footer className="vajra-footer">
        <div className="vajra-container">
          <div className="public-footer-layout">
            <a href="#hero" className="public-footer-brand" aria-label="VAJRA home">
              <img src="/vajra-logo.png" alt="VAJRA" className="footer-logo-img" />
            </a>
            <nav className="public-footer-nav" aria-label="Footer navigation">
              <a href="#journey">How It Works</a>
              <a href="#services">Services</a>
              <a href="#pricing">Pricing</a>
              <a href={GET_STARTED_HREF}>Get Started</a>
            </nav>
            <a className="public-footer-email" href="mailto:vajra.techworks@gmail.com">{CONTACT_EMAIL}</a>
          </div>
          <div className="footer-sub-bar">
            <span>© 2026 VAJRA. All rights reserved.</span>
            <span>For cafés and restaurants.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
