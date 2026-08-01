import argparse
import asyncio
import json
from pathlib import Path

import edge_tts
import yaml

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


async def synthesize(text, out_audio_path, voice, rate, pitch):
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    word_boundaries = []

    with open(out_audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_boundaries.append(
                    {
                        "text": chunk["text"],
                        "offset_ms": chunk["offset"] / 10000,
                        "duration_ms": chunk["duration"] / 10000,
                    }
                )

    return word_boundaries


def generate_tts_for_script(script_path, config):
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    audio_dir = Path(__file__).parent / config["paths"]["audio_dir"]
    audio_dir.mkdir(parents=True, exist_ok=True)

    video_id = script["id"]
    audio_path = audio_dir / f"{video_id}.mp3"
    boundaries_path = audio_dir / f"{video_id}_words.json"

    voice = config["tts"]["voice"]
    rate = config["tts"]["rate"]
    pitch = config["tts"]["pitch"]

    word_boundaries = asyncio.run(
        synthesize(script["script_text"], audio_path, voice, rate, pitch)
    )

    with open(boundaries_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "video_id": video_id,
                "voice": voice,
                "word_boundaries": word_boundaries,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    return audio_path, boundaries_path


def main():
    parser = argparse.ArgumentParser(description="Generate TTS audio for a video script.")
    parser.add_argument("script_path", help="Path to the script JSON file")
    args = parser.parse_args()

    config = load_config()
    audio_path, boundaries_path = generate_tts_for_script(args.script_path, config)

    print(f"Audio saved to: {audio_path}")
    print(f"Word boundaries saved to: {boundaries_path}")


if __name__ == "__main__":
    main()
