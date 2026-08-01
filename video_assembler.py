import argparse
import json
import shutil
from pathlib import Path

import ffmpeg
import yaml

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_ffmpeg_available():
    if shutil.which("ffmpeg") is None:
        raise EnvironmentError(
            "ffmpeg was not found on PATH. Install it (e.g. `winget install ffmpeg` "
            "or from https://ffmpeg.org/download.html) before assembling videos."
        )


def format_ass_time(ms):
    total_seconds = ms / 1000
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60
    centiseconds = int((seconds - int(seconds)) * 100)
    return f"{hours}:{minutes:02d}:{int(seconds):02d}.{centiseconds:02d}"


def build_ass_subtitles(word_boundaries, config, ass_path):
    resolution = config["video"]["resolution"]
    font_size = config["captions"]["font_size"]

    # Allineato allo standard qualitativo degli altri account (CertSprint/PC
    # Tweaker/SoloFounded/Shopify): font Poppins ExtraBold bundlato (non il
    # generico Arial-Bold di prima), gruppi da 2 parole invece di 4 (ritmo
    # "flash caption" a piu' alta retention gia' validato altrove) e un
    # piccolo pop-in di scala su ogni gruppo invece di testo statico.
    font = config["captions"]["font"]
    words_per_group = 2
    groups = [
        word_boundaries[i : i + words_per_group]
        for i in range(0, len(word_boundaries), words_per_group)
    ]

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {resolution[0]}
PlayResY: {resolution[1]}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Alignment, MarginL, MarginR, MarginV, Outline, Shadow
Style: Default,{font},{font_size},&H00FFFFFF,&H00000000,&H80000000,-1,2,80,80,260,6,0

[Events]
Format: Layer, Start, End, Style, Text
"""

    lines = []
    for group in groups:
        if not group:
            continue
        start_ms = group[0]["offset_ms"]
        end_ms = group[-1]["offset_ms"] + group[-1]["duration_ms"]
        text = " ".join(w["text"] for w in group)
        # Pop-in: parte leggermente piu' piccola e scatta a scala piena nei
        # primi 120ms - stesso principio del CAPTION_POP_SECONDS usato nelle
        # pipeline moviepy, qui espresso come ASS override tag \t (transform).
        pop = r"{\fscx85\fscy85\t(0,120,\fscx100\fscy100)}"
        lines.append(
            f"Dialogue: 0,{format_ass_time(start_ms)},{format_ass_time(end_ms)},Default,{pop}{text}"
        )

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(lines))

    return ass_path


def assemble_video(avatar_video_path, word_boundaries_path, script_path, config, output_dir=None):
    check_ffmpeg_available()

    with open(word_boundaries_path, "r", encoding="utf-8") as f:
        boundaries_data = json.load(f)
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    video_id = script["id"]
    final_dir = Path(output_dir) if output_dir else Path(__file__).parent / config["paths"]["final_dir"]
    final_dir.mkdir(parents=True, exist_ok=True)

    ass_path = final_dir / f"{video_id}.ass"
    build_ass_subtitles(boundaries_data["word_boundaries"], config, ass_path)

    resolution = config["video"]["resolution"]
    output_path = final_dir / f"{video_id}.mp4"

    # ffmpeg-python double-escapes a filter's *positional* argument (adds
    # extra backslashes on top of its own colon-escaping), which breaks on
    # this project's folder path ("AI Avatars Bot" - both a space and a
    # drive-letter colon). Passing it as the "filename" keyword instead goes
    # through the normal single-escaping path and works correctly.
    ass_path_str = str(ass_path).replace("\\", "/")
    fonts_dir = str(Path(__file__).parent / "assets" / "fonts").replace("\\", "/")

    # A chain of only .filter() calls carries the VIDEO stream alone into
    # .output() - the source's audio track was never pulled into the graph,
    # so it silently got dropped from every rendered video (confirmed live
    # 2026-08-01: bozze arrivavano mute). Grab the same input's .audio
    # explicitly and pass both streams to output().
    input_stream = ffmpeg.input(str(avatar_video_path))
    video = (
        input_stream.video
        .filter("scale", resolution[0], resolution[1], force_original_aspect_ratio="decrease")
        .filter("pad", resolution[0], resolution[1], "(ow-iw)/2", "(oh-ih)/2", color=config["branding"]["frame_color"])
        .filter("subtitles", filename=ass_path_str, fontsdir=fonts_dir)
    )
    audio = input_stream.audio

    (
        ffmpeg.output(video, audio, str(output_path), vcodec="libx264", acodec="aac", pix_fmt="yuv420p", movflags="faststart")
        .overwrite_output()
        .run(quiet=True)
    )

    metadata_path = final_dir / f"{video_id}_metadata.json"
    metadata = {
        "id": video_id,
        "title": script["title"],
        "caption": script["caption"],
        "hashtags": script["hashtags"],
        "category": script["category"],
        "video_path": str(output_path),
    }
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return output_path, metadata_path


def main():
    parser = argparse.ArgumentParser(description="Assemble final short-form video with burned-in captions.")
    parser.add_argument("avatar_video_path", help="Path to the SadTalker-rendered avatar video")
    parser.add_argument("word_boundaries_path", help="Path to the *_words.json file from tts_generator.py")
    parser.add_argument("script_path", help="Path to the script JSON file")
    args = parser.parse_args()

    config = load_config()
    output_path, metadata_path = assemble_video(
        args.avatar_video_path, args.word_boundaries_path, args.script_path, config
    )

    print(f"Final video saved to: {output_path}")
    print(f"Metadata saved to: {metadata_path}")


if __name__ == "__main__":
    main()
