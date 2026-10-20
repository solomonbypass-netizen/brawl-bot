import React from "react";
import { Composition } from "remotion";
import { BrawlPromoVideo } from "./BrawlPromoVideo";

export const Root: React.FC = () => {
  // Total frames: 144 + 96 + 111 + 165 = 516 frames (17.2s at 30 fps)
  // Perfectly calibrated to the natural rhythm of high-fidelity voiceover
  return (
    <>
      <Composition
        id="BrawlStarsPromo"
        component={BrawlPromoVideo}
        durationInFrames={516}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          channelName: "solomon",
          channelLink: "@solomon",
          oldPrice: "5 000 РУБ.",
          newPrice: "490 РУБ.",
          trophies: "50 000+",
          brawlersInfo: "ВСЕ ЛЕГЕНДАРКИ",
        }}
      />
    </>
  );
};
