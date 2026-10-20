import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";

interface GlowTextProps {
  children: React.ReactNode;
  delay?: number;
  highlightWords?: string[];
  fontSize?: number;
  color?: string;
  glowColor?: string;
}

export const GlowText: React.FC<GlowTextProps> = ({
  children,
  delay = 0,
  fontSize = 86,
  color = "#ffffff",
  glowColor = "rgba(99, 102, 241, 0.8)",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame: frame - delay,
    fps,
    config: {
      damping: 14,
      stiffness: 120,
    },
  });

  const scale = progress;
  const opacity = Math.min(1, Math.max(0, progress * 1.2));
  const translateY = (1 - progress) * 35;

  return (
    <div
      style={{
        transform: `translateY(${translateY}px) scale(${scale})`,
        opacity,
        textAlign: "center",
        fontFamily: "'Inter', 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        fontWeight: 900,
        fontSize,
        lineHeight: 1.1,
        letterSpacing: "-0.04em",
        color,
        textShadow: `
          0 0 20px ${glowColor},
          0 0 45px rgba(99, 102, 241, 0.45)
        `,
        padding: "0 40px",
        willChange: "transform, opacity",
      }}
    >
      {children}
    </div>
  );
};
