import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { GlowText } from "../components/GlowText";

export const HookScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const badgeSpring = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 120 },
  });

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* Top Glassmorphic Pill Badge */}
      <div
        style={{
          position: "absolute",
          top: 180,
          transform: `scale(${badgeSpring})`,
          opacity: badgeSpring,
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "12px 28px",
          borderRadius: 9999,
          backgroundColor: "rgba(24, 24, 27, 0.75)",
          border: "1px solid rgba(99, 102, 241, 0.35)",
          boxShadow: "0 0 25px rgba(99, 102, 241, 0.25)",
          backdropFilter: "blur(12px)",
        }}
      >
        <span style={{ fontSize: 24 }}>⚡</span>
        <span
          style={{
            fontFamily: "'Inter', sans-serif",
            fontWeight: 700,
            fontSize: 24,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "#a5b4fc",
          }}
        >
          ИНСАЙД РЫНКА
        </span>
      </div>

      {/* Synchronized Words: Appears exactly as Svetlana pronounces each chunk */}
      <div
        style={{
          position: "relative",
          minHeight: 340,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {frame < 42 && (
          <GlowText delay={0} fontSize={98}>
            BRAWL STARS
          </GlowText>
        )}

        {frame >= 42 && frame < 84 && (
          <GlowText
            delay={42}
            fontSize={116}
            color="#f43f5e"
            glowColor="rgba(244, 63, 94, 0.9)"
          >
            УХОДИТ?
          </GlowText>
        )}

        {frame >= 84 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12, alignItems: "center" }}>
            <GlowText delay={84} fontSize={74} color="#e0e7ff">
              ИЛИ АККАУНТЫ
            </GlowText>
            <GlowText
              delay={96}
              fontSize={86}
              color="#818cf8"
              glowColor="rgba(129, 140, 248, 0.9)"
            >
              ОБЕСЦЕНИЛИСЬ?
            </GlowText>
          </div>
        )}
      </div>
    </div>
  );
};
