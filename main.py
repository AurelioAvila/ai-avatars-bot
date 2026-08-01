import argparse
from pathlib import Path

from publisher import publish
from script_generator import generate_script, save_script, load_config as load_script_config
from tts_generator import generate_tts_for_script
from video_assembler import assemble_video

BASE_DIR = Path(__file__).parent


def run_pipeline(category=None, seed=None, skip_avatar_wait=False):
    config = load_script_config()

    print("Step 1/4: Generating script...")
    script_data = generate_script(config, category=category, seed=seed)
    script_path = save_script(script_data, config)
    print(f"  Script saved: {script_path}")

    print("Step 2/4: Generating TTS audio...")
    audio_path, boundaries_path = generate_tts_for_script(script_path, config)
    print(f"  Audio saved: {audio_path}")
    print(f"  Word boundaries saved: {boundaries_path}")

    print("Step 3/4: Avatar lip-sync via Google Colab (SadTalker).")
    print("  This step runs on Colab's free GPU, not locally. To continue:")
    print(f"    1. Run: python drive_sync.py upload --audio-path \"{audio_path}\"")
    print("    2. Open colab/avatar_lipsync.ipynb in Google Colab and click Run All.")
    print("       (Point it at the same avatar image and the uploaded audio file.)")
    print(f"    3. Run: python drive_sync.py poll --video-id {script_data['id']} --dest output/audio/{script_data['id']}_avatar.mp4")
    print("       This polls the Drive outbox folder and downloads the rendered video once ready.")
    print(
        "  Colab's free tier does not support reliable unattended scheduled execution, "
        "so this step currently requires manually opening the notebook and clicking Run All."
    )

    if skip_avatar_wait:
        print("  --skip-avatar-wait was set, stopping here. Run video_assembler.py manually once the avatar video is downloaded.")
        return

    avatar_video_path = input(
        "Once the avatar video has been downloaded, paste its file path here (or leave blank to stop): "
    ).strip()

    if not avatar_video_path:
        print("No avatar video path provided. Stopping before final assembly.")
        return

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
    parser.add_argument(
        "--skip-avatar-wait",
        action="store_true",
        help="Stop after generating script/audio instead of waiting for the Colab step interactively",
    )
    args = parser.parse_args()

    run_pipeline(category=args.category, seed=args.seed, skip_avatar_wait=args.skip_avatar_wait)


if __name__ == "__main__":
    main()
