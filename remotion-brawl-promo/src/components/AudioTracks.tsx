import React from "react";
import { Audio, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

export const AudioTracks: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Smooth fade-out of background music during final 1.5 seconds
  const musicVolume = interpolate(
    frame,
    [0, durationInFrames - 45, durationInFrames],
    [0.18, 0.18, 0],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  return (
    <>
      {/* 1. Primary AI Voiceover Track */}
      <Audio
        src={staticFile("audio/voice.mp3")}
        volume={1.0}
      />

      {/* 2. Cinematic Lo-Fi / Bass Background Music Track */}
      <Audio
        src={staticFile("audio/background-music.mp3")}
        volume={musicVolume}
      />
    </>
  );
};
