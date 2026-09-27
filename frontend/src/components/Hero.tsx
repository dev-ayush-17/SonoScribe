import React, { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { Mic, Zap, BrainCircuit, FileText, ArrowRight } from 'lucide-react';

interface Props {
  onGetStarted: () => void;
}

const FEATURE_PILLS = [
  { icon: <Mic size={13} />, text: 'Live Transcription', color: 'var(--accent-cyan)' },
  { icon: <BrainCircuit size={13} />, text: 'AI Meeting Notes', color: 'var(--accent-violet)' },
  { icon: <FileText size={13} />, text: 'Auto Doc Export', color: 'var(--accent-teal)' },
  { icon: <Zap size={13} />, text: '100% Local Privacy', color: 'var(--accent-amber)' },
];

export const Hero: React.FC<Props> = ({ onGetStarted }) => {
  const heroRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const pillsRef = useRef<HTMLDivElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!heroRef.current) return;

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

      tl.fromTo(
        titleRef.current,
        { opacity: 0, y: 40, filter: 'blur(8px)' },
        { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.9 }
      )
        .fromTo(
          subtitleRef.current,
          { opacity: 0, y: 24 },
          { opacity: 1, y: 0, duration: 0.7 },
          '-=0.5'
        )
        .fromTo(
          pillsRef.current?.children ? Array.from(pillsRef.current.children) : [],
          { opacity: 0, y: 16, scale: 0.92 },
          { opacity: 1, y: 0, scale: 1, duration: 0.5, stagger: 0.08 },
          '-=0.4'
        )
        .fromTo(
          ctaRef.current,
          { opacity: 0, y: 20 },
          { opacity: 1, y: 0, duration: 0.6 },
          '-=0.3'
        );
    }, heroRef);

    return () => ctx.revert();
  }, []);

  return (
    <div
      ref={heroRef}
      className="hero-section"
    >
      {/* Decorative accent line at top */}
      <div className="hero-accent-line" />

      <div className="hero-content">
        {/* Badge */}
        <div className="hero-badge">
          <span className="hero-badge-dot" />
          <span>Real-time AI Meeting Intelligence</span>
        </div>

        {/* Main Title */}
        <h1 ref={titleRef} className="hero-title">
          Your Meetings,{' '}
          <span className="hero-title-gradient">
            Transcribed & Distilled
          </span>
        </h1>

        {/* Subtitle */}
        <p ref={subtitleRef} className="hero-subtitle">
          SonoScribe captures every word in real-time, then transforms hours of discussion
          into crisp minutes, action items, and key insights — completely on your machine.
        </p>

        {/* Feature Pills */}
        <div ref={pillsRef} className="hero-pills">
          {FEATURE_PILLS.map((pill, i) => (
            <div key={i} className="hero-pill" style={{ '--pill-color': pill.color } as React.CSSProperties}>
              <span className="hero-pill-icon" style={{ color: pill.color }}>{pill.icon}</span>
              <span>{pill.text}</span>
            </div>
          ))}
        </div>

        {/* CTA */}
        <div ref={ctaRef} className="hero-cta">
          <button className="hero-cta-primary" onClick={onGetStarted}>
            <Mic size={18} />
            Open Recording Studio
            <ArrowRight size={16} className="hero-cta-arrow" />
          </button>
          <div className="hero-cta-hint">
            No cloud. No signup. Runs entirely locally.
          </div>
        </div>
      </div>

      {/* Decorative floating waveform visual */}
      <div className="hero-visual" aria-hidden="true">
        <div className="hero-wave-container">
          {Array.from({ length: 32 }).map((_, i) => (
            <div
              key={i}
              className="hero-wave-bar"
              style={{
                animationDelay: `${(i * 0.09) % 1.5}s`,
                height: `${20 + Math.sin(i * 0.7) * 18 + Math.cos(i * 0.4) * 12}px`,
              }}
            />
          ))}
        </div>
        <div className="hero-visual-label">Live Audio Stream</div>
      </div>
    </div>
  );
};
