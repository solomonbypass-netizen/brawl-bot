import React from "react";
import { Audio, interpolate, Sequence, staticFile } from "remotion";
import { Background } from "./components/Background";
import { HookScene } from "./scenes/HookScene";
import { PainScene } from "./scenes/PainScene";
import { SolutionScene } from "./scenes/SolutionScene";
import { CTAScene } from "./scenes/CTAScene";

interface BrawlPromoVideoProps {
  channelName?: string;
  channelLink?: string;
  oldPrice?: string;
  newPrice?: string;
  trophies?: string;
  brawlersInfo?: string;
}

export const BrawlPromoVideo: React.FC<BrawlPromoVideoProps> = ({
  channelName = "solomon",
  channelLink = "@solomon",
  oldPrice = "5 000 РУБ.",
  newPrice = "490 РУБ.",
  trophies = "50 000+",
  brawlersInfo = "ВСЕ ЛЕГЕНДАРКИ",
}) => {
  // Calibrated frame durations matching each scene's pleasant speech snippet
  const S1_DURATION = 144; // 4.80s
  const S2_DURATION = 96;  // 3.20s
  const S3_DURATION = 111; // 3.70s
  const S4_DURATION = 165; // 5.50s
  const TOTAL_FRAMES = S1_DURATION + S2_DURATION + S3_DURATION + S4_DURATION; // 516 frames

  return (
    <div
      style={{
        position: "relative",
        width: 1080,
        height: 1920,
        backgroundColor: "#09090b",
        fontFamily: "'Inter', sans-serif",
      }}
    >
      {/* 1. Global Cinematic Background Beat with Smooth Audio Ducking */}
      <Audio
        src={staticFile("audio/background-music.mp3")}
        volume={(f) =>
          interpolate(
            f,
            [0, TOTAL_FRAMES - 45, TOTAL_FRAMES],
            [0.16, 0.16, 0],
            { extrapolateRight: "clamp" }
          )
        }
      />

      {/* 2. Apple / Linear Dark Grid & Ambient Glows */}
      <Background />

      {/* 3. Scene 1: Hook (0 to 144 frames) - ZERO LAG */}
      <Sequence from={0} durationInFrames={S1_DURATION}>
        <Audio src={staticFile("audio/scene1_voice.mp3")} volume={1.0} />
        <HookScene />
      </Sequence>

      {/* 4. Scene 2: Pain & Market Shock (144 to 240 frames) - Starts right on time */}
      <Sequence from={S1_DURATION} durationInFrames={S2_DURATION}>
        <Audio src={staticFile("audio/scene2_voice.mp3")} volume={1.0} />
        <PainScene />
      </Sequence>

      {/* 5. Scene 3: Solution & Price Drop (240 to 351 frames) - Frame-accurate sync */}
      <Sequence from={S1_DURATION + S2_DURATION} durationInFrames={S3_DURATION}>
        <Audio src={staticFile("audio/scene3_voice.mp3")} volume={1.0} />
        <SolutionScene
          oldPrice={oldPrice}
          newPrice={newPrice}
          trophies={trophies}
          brawlersInfo={brawlersInfo}
        />
      </Sequence>

      {/* 6. Scene 4: Call To Action & Scarcity (351 to 516 frames) */}
      <Sequence from={S1_DURATION + S2_DURATION + S3_DURATION} durationInFrames={S4_DURATION}>
        <Audio src={staticFile("audio/scene4_voice.mp3")} volume={1.0} />
        <CTAScene channelName={channelName} channelLink={channelLink} />
      </Sequence>
    </div>
  );
};
