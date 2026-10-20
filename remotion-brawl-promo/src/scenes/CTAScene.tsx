import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { GlowText } from "../components/GlowText";

interface CTASceneProps {
  channelName?: string;
  channelLink?: string;
}

export const CTAScene: React.FC<CTASceneProps> = ({
  channelName = "solomon",
  channelLink = "@solomon",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const qrSpring = spring({
    frame: frame - 4,
    fps,
    config: { damping: 14, stiffness: 120 },
  });

  const pulse = interpolate(
    Math.sin((frame / 12) * Math.PI),
    [-1, 1],
    [0.85, 1.15]
  );

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
      <div style={{ marginBottom: 32 }}>
        <GlowText delay={0} fontSize={68} color="#ffffff">
          ЗАБИРАЙ СВОЙ
        </GlowText>
      </div>

      {/* Sleek Neon QR Container */}
      <div
        style={{
          transform: `scale(${qrSpring})`,
          opacity: qrSpring,
          background: "linear-gradient(180deg, rgba(24, 24, 27, 0.95) 0%, rgba(9, 9, 11, 0.98) 100%)",
          border: "2px solid rgba(99, 102, 241, 0.8)",
          borderRadius: 44,
          padding: 32,
          boxShadow: `
            0 0 ${40 * pulse}px rgba(99, 102, 241, 0.6),
            0 25px 60px rgba(0, 0, 0, 0.9)
          `,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 22,
        }}
      >
        <div
          style={{
            background: "#ffffff",
            padding: 22,
            borderRadius: 28,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <svg
            width="300"
            height="300"
            viewBox="0 0 100 100"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <rect x="10" y="10" width="28" height="28" rx="6" fill="#09090b" />
            <rect x="16" y="16" width="16" height="16" rx="3" fill="#ffffff" />
            <rect x="20" y="20" width="8" height="8" rx="2" fill="#4f46e5" />

            <rect x="62" y="10" width="28" height="28" rx="6" fill="#09090b" />
            <rect x="68" y="16" width="16" height="16" rx="3" fill="#ffffff" />
            <rect x="72" y="20" width="8" height="8" rx="2" fill="#4f46e5" />

            <rect x="10" y="62" width="28" height="28" rx="6" fill="#09090b" />
            <rect x="16" y="68" width="16" height="16" rx="3" fill="#ffffff" />
            <rect x="20" y="72" width="8" height="8" rx="2" fill="#4f46e5" />

            <rect x="44" y="12" width="8" height="8" rx="2" fill="#09090b" />
            <rect x="44" y="26" width="8" height="14" rx="2" fill="#4f46e5" />
            <rect x="12" y="46" width="14" height="8" rx="2" fill="#09090b" />
            <rect x="32" y="46" width="8" height="8" rx="2" fill="#09090b" />
            <rect x="46" y="46" width="12" height="12" rx="3" fill="#4f46e5" />
            <rect x="64" y="46" width="10" height="8" rx="2" fill="#09090b" />
            <rect x="80" y="46" width="8" height="12" rx="2" fill="#09090b" />
            <rect x="46" y="66" width="8" height="14" rx="2" fill="#09090b" />
            <rect x="64" y="64" width="14" height="8" rx="2" fill="#4f46e5" />
            <rect x="64" y="78" width="24" height="10" rx="3" fill="#09090b" />
          </svg>
        </div>

        {/* Telegram Username Badge */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            background: "rgba(99, 102, 241, 0.2)",
            border: "1px solid rgba(99, 102, 241, 0.5)",
            padding: "10px 30px",
            borderRadius: 9999,
          }}
        >
          <span style={{ fontSize: 24, color: "#818cf8" }}>✈️</span>
          <span
            style={{
              fontFamily: "'Inter', sans-serif",
              fontWeight: 800,
              fontSize: 32,
              color: "#ffffff",
            }}
          >
            {channelLink}
          </span>
        </div>
      </div>

      {/* Scarcity Countdown Pill */}
      <div
        style={{
          marginTop: 34,
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "14px 34px",
          borderRadius: 9999,
          background: "linear-gradient(90deg, rgba(239, 68, 68, 0.25) 0%, rgba(245, 158, 11, 0.25) 100%)",
          border: "1px solid rgba(239, 68, 68, 0.5)",
          boxShadow: "0 0 30px rgba(239, 68, 68, 0.3)",
        }}
      >
        <span style={{ fontSize: 24 }}>🔥</span>
        <span
          style={{
            fontFamily: "'Inter', sans-serif",
            fontWeight: 800,
            fontSize: 28,
            color: "#fecaca",
            letterSpacing: "0.04em",
          }}
        >
          ОСТАЛОСЬ ВСЕГО 3 МЕСТА
        </span>
      </div>

      <div style={{ marginTop: 22 }}>
        <span
          style={{
            fontFamily: "'Inter', sans-serif",
            fontWeight: 600,
            fontSize: 26,
            color: "#a1a1aa",
          }}
        >
          ССЫЛКА В ШАПКЕ ПРОФИЛЯ ↗
        </span>
      </div>
    </div>
  );
};
