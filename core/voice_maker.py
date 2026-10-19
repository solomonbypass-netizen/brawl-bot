import os
import asyncio
import logging
import edge_tts

logger = logging.getLogger("VoiceMaker")

DEFAULT_VOICE = "ru-RU-DmitryNeural"

async def _synthesize(text, output_file, voice=DEFAULT_VOICE):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def generate_voiceover_audio(text, output_file, voice=DEFAULT_VOICE):
    """
    Synthesizes realistic, energetic Russian neural voiceover.
    Returns True if successfully created, False on failure.
    """
    try:
        asyncio.run(_synthesize(text, output_file, voice))
        if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
            logger.info(f"Synthesized voiceover: {output_file} ({os.path.getsize(output_file)} bytes)")
            return True
    except Exception as e:
        logger.warning(f"Voice synthesis failed ({e}), continuing without speech...")
    return False
