import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { GlowText } from "../components/GlowText";

export const PainScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const metricSpring = spring({
    frame: frame - 38,
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
      {/* Top Danger Header */}
      <div
        style={{
          position: "absolute",
          top: 180,
          padding: "12px 28px",
          borderRadius: 9999,
          backgroundColor: "rgba(39, 39, 42, 0.75)",
          border: "1px solid rgba(244, 63, 94, 0.35)",
          boxShadow: "0 0 25px rgba(244, 63, 94, 0.2)",
          backdropFilter: "blur(12px)",
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}
      >
        <span style={{ fontSize: 22 }}>⚠️</span>
        <span
          style={{
            fontFamily: "'Inter', sans-serif",
            fontWeight: 700,
            fontSize: 22,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "#fda4af",
          }}
        >
          ОФИЦИАЛЬНЫЙ ШОП
        </span>
      </div>

      {/* Main Kinetic Sequence: Synced to 'Цены в официальном магазине взлетели в три раза' */}
      <div
        style={{
          position: "relative",
          minHeight: 340,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {frame < 38 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14, alignItems: "center" }}>
            <GlowText delay={0} fontSize={80}>
              РАЗРАБОТЧИКИ
            </GlowText>
            <GlowText
              delay={12}
              fontSize={86}
              color="#fb7185"
              glowColor="rgba(251, 113, 133, 0.8)"
            >
              ЗАКРУЧИВАЮТ ГАЙКИ
            </GlowText>
          </div>
        )}

        {frame >= 38 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 24, alignItems: "center" }}>
            <GlowText delay={38} fontSize={72} color="#ffffff">
              ЦЕНЫ ВЗЛЕТЕЛИ
            </GlowText>

            <div
              style={{
                transform: `scale(${metricSpring})`,
                opacity: metricSpring,
                display: "flex",
                alignItems: "center",
                gap: 16,
                padding: "16px 42px",
                borderRadius: 24,
                background: "linear-gradient(135deg, rgba(225, 29, 72, 0.25) 0%, rgba(159, 18, 57, 0.4) 100%)",
                border: "2px solid rgba(244, 63, 94, 0.7)",
                boxShadow: "0 0 50px rgba(225, 29, 72, 0.4)",
              }}
            >
              <span
                style={{
                  fontFamily: "'Inter', sans-serif",
                  fontWeight: 900,
                  fontSize: 104,
                  letterSpacing: "-0.04em",
                  color: "#ffffff",
                  textShadow: "0 0 35px rgba(255, 255, 255, 0.8)",
                }}
              >
                В 3 РАЗА!
              </span>
            </div>

            <span
              style={{
                fontFamily: "'Inter', sans-serif",
                fontWeight: 600,
                fontSize: 32,
                color: "#a1a1aa",
                letterSpacing: "0.02em",
              }}
            >
              Донат в игре стал неподъемным
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
