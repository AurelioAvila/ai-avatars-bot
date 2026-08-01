import argparse
from pathlib import Path

from lipsync_local import generate_avatar_video
from publisher import publish
from script_generator import generate_script, save_script, load_config as load_script_config
from tts_generator import generate_tts_for_script
from video_assembler import assemble_video

BASE_DIR = Path(__file__).parent


def run_pipeline(category=None, seed=None):
    config = load_script_config()

    print("Step 1/4: Generating script...")
    script_data = generate_script(config, category=category, seed=seed)
    script_path = save_script(script_data, config)
    print(f"  Script saved: {script_path}")

    print("Step 2/4: Generating TTS audio...")
    audio_path, boundaries_path = generate_tts_for_script(script_path, config)
    print(f"  Audio saved: {audio_path}")
    print(f"  Word boundaries saved: {boundaries_path}")

    print("Step 3/4: Avatar lip-sync (local Wav2Lip, GTX 1660)...")
    avatar_image = BASE_DIR / config["paths"]["avatar_image"]
    avatar_video_path = generate_avatar_video(str(avatar_image), str(audio_path))
    print(f"  Avatar video: {avatar_video_path}")

    print("Step 4/4: Assembling final video with captions...")
    output_path, metadata_path = assemble_video(avatar_video_path, boundaries_path, script_path, config)
    print(f"  Final video: {output_path}")
    print(f"  Metadata: {metadata_path}")

    print("Step 5/5: Publishing to YouTube/Instagram/TikTok...")
    try:
        results = publish(str(output_path), str(metadata_path))
        print(f"  Publish results: {results}")
    except Exception as exc:
        print(f"  ! Pubblicazione automatica non ancora disponibile ({exc})")
        print(f"  Carica manualmente {output_path} usando i metadati in {metadata_path}.")


def main():
    parser = argparse.ArgumentParser(description="Run the full AI Avatars Bot pipeline.")
    parser.add_argument("--category", help="Force a specific script category")
    parser.add_argument("--seed", type=int, help="Random seed for script generation")
    args = parser.parse_args()

    run_pipeline(category=args.category, seed=args.seed)


if __name__ == "__main__":
    main()
