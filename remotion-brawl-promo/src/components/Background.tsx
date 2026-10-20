import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

export const Background: React.FC = () => {
  const frame = useCurrentFrame();

  // Subtle breathing pulse for ambient glow
  const glowScale = interpolate(
    Math.sin((frame / 30) * Math.PI),
    [-1, 1],
    [0.92, 1.08]
  );
  const glowOpacity = interpolate(
    Math.sin((frame / 25) * Math.PI),
    [-1, 1],
    [0.35, 0.55]
  );

  return (
    <div
      style={{
        position: "absolute",
        width: "100%",
        height: "100%",
        backgroundColor: "#09090b", // zinc-950
        overflow: "hidden",
      }}
    >
      {/* 1. Linear-style Grid Overlay */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `
            linear-gradient(to right, rgba(255, 255, 255, 0.035) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.035) 1px, transparent 1px)
          `,
          backgroundSize: "60px 60px",
          maskImage: "radial-gradient(ellipse at center, black 40%, transparent 80%)",
          WebkitMaskImage: "radial-gradient(ellipse at center, black 40%, transparent 80%)",
        }}
      />

      {/* 2. Top-Center Ambient Indigo/Violet Glow */}
      <div
        style={{
          position: "absolute",
          top: "15%",
          left: "50%",
          width: 750,
          height: 750,
          transform: `translate(-50%, -50%) scale(${glowScale})`,
          background: "radial-gradient(circle, rgba(99, 102, 241, 0.45) 0%, rgba(139, 92, 246, 0.15) 50%, transparent 70%)",
          filter: "blur(90px)",
          opacity: glowOpacity,
          pointerEvents: "none",
        }}
      />

      {/* 3. Bottom Accent Cyan/Indigo Glow */}
      <div
        style={{
          position: "absolute",
          bottom: "10%",
          left: "50%",
          width: 650,
          height: 650,
          transform: "translate(-50%, 50%)",
          background: "radial-gradient(circle, rgba(79, 70, 229, 0.35) 0%, rgba(14, 165, 233, 0.12) 50%, transparent 70%)",
          filter: "blur(110px)",
          opacity: 0.4,
          pointerEvents: "none",
        }}
      />

      {/* 4. Elegant Vignette */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "radial-gradient(circle at center, transparent 40%, rgba(9, 9, 11, 0.75) 100%)",
          pointerEvents: "none",
        }}
      />
    </div>
  );
};
