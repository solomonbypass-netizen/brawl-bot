import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { GlowText } from "../components/GlowText";

interface SolutionSceneProps {
  oldPrice?: string;
  newPrice?: string;
  trophies?: string;
  brawlersInfo?: string;
}

export const SolutionScene: React.FC<SolutionSceneProps> = ({
  oldPrice = "5 000 РУБ.",
  newPrice = "490 РУБ.",
  trophies = "50 000+",
  brawlersInfo = "ВСЕ ЛЕГЕНДАРКИ",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const cardSpring = spring({
    frame: frame - 4,
    fps,
    config: { damping: 14, stiffness: 120 },
  });

  const priceSpring = spring({
    frame: frame - 32,
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
        padding: "0 40px",
      }}
    >
      <div style={{ marginBottom: 36 }}>
        <GlowText delay={0} fontSize={64} color="#ffffff">
          УМНЫЕ ИГРОКИ
        </GlowText>
      </div>

      {/* Apple / Linear Glassmorphic Account Card */}
      <div
        style={{
          width: "100%",
          maxWidth: 920,
          transform: `scale(${cardSpring}) translateY(${(1 - cardSpring) * 60}px)`,
          opacity: cardSpring,
          background: "linear-gradient(180deg, rgba(24, 24, 27, 0.85) 0%, rgba(9, 9, 11, 0.95) 100%)",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          borderRadius: 40,
          padding: "44px 40px",
          boxShadow: `
            0 25px 70px rgba(0, 0, 0, 0.7),
            0 0 50px rgba(99, 102, 241, 0.25)
          `,
          backdropFilter: "blur(24px)",
          display: "flex",
          flexDirection: "column",
          gap: 28,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div
              style={{
                width: 16,
                height: 16,
                borderRadius: "50%",
                backgroundColor: "#10b981",
                boxShadow: "0 0 14px #10b981",
              }}
            />
            <span
              style={{
                fontFamily: "'Inter', sans-serif",
                fontWeight: 800,
                fontSize: 26,
                letterSpacing: "0.06em",
                color: "#e4e4e7",
              }}
            >
              ПРИВАТНЫЙ ЛОТ #842
            </span>
          </div>

          <div
            style={{
              padding: "8px 20px",
              borderRadius: 9999,
              backgroundColor: "rgba(16, 185, 129, 0.15)",
              border: "1px solid rgba(16, 185, 129, 0.4)",
              color: "#34d399",
              fontFamily: "'Inter', sans-serif",
              fontWeight: 700,
              fontSize: 20,
            }}
          >
            100% ВЕРИФИКАЦИЯ
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <div
            style={{
              background: "rgba(39, 39, 42, 0.5)",
              borderRadius: 24,
              padding: "20px 24px",
              border: "1px solid rgba(255, 255, 255, 0.06)",
            }}
          >
            <div style={{ fontSize: 22, color: "#a1a1aa", fontWeight: 600, marginBottom: 8 }}>
              Кубки основы
            </div>
            <div
              style={{
                fontFamily: "'Inter', sans-serif",
                fontWeight: 900,
                fontSize: 48,
                color: "#fbbf24",
                textShadow: "0 0 25px rgba(251, 191, 36, 0.4)",
              }}
            >
              {trophies}
            </div>
          </div>

          <div
            style={{
              background: "rgba(39, 39, 42, 0.5)",
              borderRadius: 24,
              padding: "20px 24px",
              border: "1px solid rgba(255, 255, 255, 0.06)",
            }}
          >
            <div style={{ fontSize: 22, color: "#a1a1aa", fontWeight: 600, marginBottom: 8 }}>
              Инвентарь
            </div>
            <div
              style={{
                fontFamily: "'Inter', sans-serif",
                fontWeight: 900,
                fontSize: 36,
                color: "#38bdf8",
                textShadow: "0 0 25px rgba(56, 189, 248, 0.4)",
              }}
            >
              {brawlersInfo}
            </div>
          </div>
        </div>

        {/* Dynamic Price Drop */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            paddingTop: 12,
            borderTop: "1px solid rgba(255, 255, 255, 0.08)",
          }}
        >
          <span
            style={{
              fontFamily: "'Inter', sans-serif",
              fontWeight: 700,
              fontSize: 40,
              color: "#71717a",
              textDecoration: "line-through",
            }}
          >
            {oldPrice}
          </span>

          <span
            style={{
              transform: `scale(${priceSpring})`,
              opacity: priceSpring,
              fontFamily: "'Inter', sans-serif",
              fontWeight: 900,
              fontSize: 76,
              color: "#10b981",
              textShadow: "0 0 40px rgba(16, 185, 129, 0.6)",
              letterSpacing: "-0.04em",
            }}
          >
            {newPrice}
          </span>
        </div>
      </div>

      <div style={{ marginTop: 36 }}>
        <GlowText delay={48} fontSize={54} color="#818cf8">
          СКУПАЮТ ЗА КОПЕЙКИ
        </GlowText>
      </div>
    </div>
  );
};
