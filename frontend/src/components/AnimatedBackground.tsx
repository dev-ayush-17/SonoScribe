import React, { useEffect, useRef } from 'react';
import { gsap } from 'gsap';

const ORBS = [
  { x: 8, y: 18, size: 420, color: '#00F2FE', opacity: 0.12 },
  { x: 82, y: 12, size: 360, color: '#4FACFE', opacity: 0.10 },
  { x: 12, y: 72, size: 380, color: '#00E699', opacity: 0.08 },
  { x: 78, y: 68, size: 320, color: '#8B5CF6', opacity: 0.07 },
  { x: 52, y: 48, size: 500, color: '#10B981', opacity: 0.05 },
  { x: 35, y: 30, size: 280, color: '#4FACFE', opacity: 0.06 },
];

export const AnimatedBackground: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const orbs = containerRef.current.querySelectorAll('[data-orb]');
    const animationIds: gsap.core.Tween[] = [];

    orbs.forEach((orb, i) => {
      const el = orb as HTMLElement;
      const config = ORBS[i];
      const duration = 8 + i * 3;
      const xRange = 8 + i * 2;
      const yRange = 6 + i * 2;

      // Floating drift animation
      const tween = gsap.to(el, {
        x: `+=${xRange}%`,
        y: `+=${yRange}%`,
        duration,
        ease: 'sine.inOut',
        yoyo: true,
        repeat: -1,
        delay: i * 0.7,
      });
      animationIds.push(tween);

      // Independent opacity breathing
      gsap.to(el, {
        opacity: config.opacity * 1.8,
        duration: 4 + i * 1.5,
        ease: 'sine.inOut',
        yoyo: true,
        repeat: -1,
        delay: i * 0.5,
      });

      // Scale pulse
      gsap.to(el, {
        scale: 1.15,
        duration: 6 + i * 2,
        ease: 'sine.inOut',
        yoyo: true,
        repeat: -1,
        delay: i * 0.9,
      });
    });

    return () => {
      animationIds.forEach((t) => t.kill());
      gsap.killTweensOf('[data-orb]');
    };
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        overflow: 'hidden',
        zIndex: 0,
      }}
    >
      {/* Rich layered background gradient */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `
            radial-gradient(ellipse at 15% 40%, rgba(0, 242, 254, 0.09) 0%, transparent 55%),
            radial-gradient(ellipse at 85% 15%, rgba(79, 172, 254, 0.09) 0%, transparent 55%),
            radial-gradient(ellipse at 50% 85%, rgba(0, 230, 153, 0.07) 0%, transparent 50%),
            radial-gradient(ellipse at 70% 50%, rgba(139, 92, 246, 0.05) 0%, transparent 45%),
            linear-gradient(160deg, #08090C 0%, #0C1022 50%, #080B14 100%)
          `,
        }}
      />

      {/* Animated floating orbs */}
      {ORBS.map((orb, i) => (
        <div
          key={i}
          data-orb={i}
          style={{
            position: 'absolute',
            width: `${orb.size}px`,
            height: `${orb.size}px`,
            left: `${orb.x}%`,
            top: `${orb.y}%`,
            borderRadius: '50%',
            background: `radial-gradient(circle, ${orb.color}40 0%, transparent 70%)`,
            filter: 'blur(60px)',
            opacity: orb.opacity,
            willChange: 'transform, opacity',
            transform: 'translate(-50%, -50%)',
          }}
        />
      ))}

      {/* Subtle dot-grid pattern */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.025,
          backgroundImage: `radial-gradient(circle, rgba(255,255,255,0.6) 1px, transparent 1px)`,
          backgroundSize: '48px 48px',
        }}
      />

      {/* Top edge fade line */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '1px',
          background: 'linear-gradient(90deg, transparent, rgba(0,242,254,0.15), rgba(79,172,254,0.15), transparent)',
        }}
      />
    </div>
  );
};