# AI Avatars Bot

AI-avatar-fronted short-form content bot built around a persistent persona, **Maddie Ross** (19, college junior — see `persona.md` for her full backstory). Instead of generic finance tips, every script is a first-person "chapter" in her ongoing broke-to-built college hustle log, weaving in natural mentions of the user's own products (CertSprint, PC Tweaker, Groomlyco, Magdock) at a roughly 80/20 story-to-sponsor ratio. Generates a script, converts it to speech, lip-syncs a static avatar portrait against that speech using SadTalker on Google Colab's free GPU, and assembles a final 9:16 video with burned-in word-synced captions. Targets YouTube Shorts, TikTok, and Instagram Reels. Zero recurring cost.

## Pipeline overview

```
script_generator.py   -> output/scripts/<id>.json          (persona-voiced hook + beats + CTA + title + caption + hashtags + sponsor)
tts_generator.py       -> output/audio/<id>.mp3             (edge-tts, free, no API key)
                        -> output/audio/<id>_words.json      (word-boundary timestamps for captions)
drive_sync.py + Colab  -> output/audio/<id>_avatar.mp4       (SadTalker lip-sync, runs on Colab free T4 GPU)
video_assembler.py     -> output/final/<id>.mp4              (ffmpeg: scale/pad to 9:16 + burned-in captions)
                        -> output/final/<id>_metadata.json    (title, caption, hashtags, ready for upload)
publisher.py            (stub - not implemented yet, see below)
```

`main.py` orchestrates steps 1-2 and 4-5 automatically, and pauses/prints instructions for step 3 (the Colab step), because Colab's free tier requires a human to open the notebook and click Run All.

## Why the avatar step is semi-manual

Google Colab's free tier does not support reliable unattended/scheduled notebook execution (sessions require an active tab, disconnect after inactivity, and have no built-in cron). Every other step in this pipeline is fully automatic. The lip-sync step is the one exception: you occasionally need to open `colab/avatar_lipsync.ipynb` in a browser and click "Run all". See "Future improvements" below for paid options that remove even this step.

## One-time setup

### 1. Install dependencies

```
pip install -r requirements.txt
```

Also install ffmpeg if it's not already on your PATH (check with `ffmpeg -version`). On Windows: `winget install ffmpeg`. On Mac: `brew install ffmpeg`.

### 2. Create the avatar portrait (one-time)

See `persona.md` for who Maddie Ross is, and `avatar_asset_setup.md` for the exact image-generation prompt. Save the result as `assets/avatar.png`.

### 3. Set up Google Drive API access (free)

`drive_sync.py` uploads TTS audio to a Drive "inbox" folder and downloads the finished avatar video from a Drive "outbox" folder, so the Colab notebook can read/write without you manually dragging files around.

1. Go to https://console.cloud.google.com/ and create a new project (or reuse one).
2. Enable the "Google Drive API" for that project (APIs & Services -> Enable APIs and Services).
3. Go to APIs & Services -> Credentials -> Create Credentials -> OAuth client ID.
   - Application type: Desktop app.
4. Download the resulting JSON and save it as `credentials.json` in this project's root folder (it's gitignored).
5. Set the OAuth consent screen to "Testing" mode with your own Google account added as a test user (no verification needed for personal use).
6. The first time you run `drive_sync.py`, a browser window will open asking you to log in and approve access. This creates `token.json` locally (also gitignored) so you won't need to log in again.
7. Upload `assets/avatar.png` to the `AIAvatarsBot_Inbox` folder in your Drive (create the folder if `drive_sync.py` hasn't already created it via `python drive_sync.py upload --audio-path <any file>`), naming it exactly `avatar.png`. This is what the Colab notebook reads.

### 4. Open the Colab notebook once to confirm it works

Upload `colab/avatar_lipsync.ipynb` to https://colab.research.google.com/ (File -> Upload notebook), or open it directly from Drive once you've placed it there. Set Runtime -> Change runtime type -> T4 GPU. Do not run it yet until you have at least one audio file in the inbox folder.

## Running a full pipeline (end to end)

```
python main.py
```

This will:
1. Generate a script (random category, or pass `--category investing_basics`).
2. Generate TTS audio + word timestamps.
3. Print instructions to upload the audio to Drive and run the Colab notebook, then wait for you to paste the path to the downloaded avatar video.
4. Assemble the final captioned 9:16 video and metadata JSON in `output/final/`.

Or run steps individually:

```
python script_generator.py --category negotiation_and_career
python tts_generator.py output/scripts/<id>.json
python drive_sync.py upload --audio-path output/audio/<id>.mp3
# open colab/avatar_lipsync.ipynb in Colab, Run All
python drive_sync.py poll --video-id <id> --dest output/audio/<id>_avatar.mp4
python video_assembler.py output/audio/<id>_avatar.mp4 output/audio/<id>_words.json output/scripts/<id>.json
```

## Publishing

`publisher.py` is currently a stub. Actual YouTube/TikTok/Instagram upload automation needs OAuth apps registered for this specific project (YouTube Data API v3 app, TikTok Content Posting API app, Instagram Graph API app), which is a separate follow-up step. Until then, upload the finished mp4 from `output/final/` manually, using the title/caption/hashtags from the accompanying `_metadata.json` file.

## What's not been tested end-to-end

This project was built without local GPU or Colab access, so the SadTalker/Colab/Drive round trip has not been run start to finish. Everything up through `tts_generator.py` (script generation, TTS, word-boundary timestamps) has been sanity-checked. Before your first real video, test in this order:

1. `python script_generator.py` and confirm the JSON output looks right.
2. `python tts_generator.py output/scripts/<id>.json` and listen to the mp3.
3. Set up Drive credentials, run `python drive_sync.py upload --audio-path output/audio/<id>.mp3`, confirm the file appears in your Drive inbox folder.
4. Open the Colab notebook, confirm SadTalker installs cleanly and produces an mp4 in the outbox folder (SadTalker's install cell can be slow the first run, ~5-10 min).
5. `python drive_sync.py poll --video-id <id> --dest ...` to confirm the download works.
6. `python video_assembler.py ...` and check the burned-in captions are readable and correctly synced.

## Future improvements

- Replace the manual "open Colab and click Run All" step with a fully unattended pipeline. Options (all paid): Colab Pro/Pro+ for longer background execution, or a dedicated cloud GPU box (e.g. a cheap on-demand instance) running SadTalker as a persistent service.
- `colab-cli` or similar tools can programmatically trigger notebook runs, but Colab's terms and free-tier limits make this unreliable for scheduled/unattended use - noted here as a stretch goal, not implemented.
- Implement `publisher.py` once platform OAuth apps exist for this project.
- Consider swapping SadTalker for a newer open-source lip-sync model if one emerges with better quality/free-tier Colab performance.

## License notes

SadTalker is used unmodified from https://github.com/OpenTalker/SadTalker (Apache 2.0 license per its repo). Check that repo's LICENSE file for the current terms before commercial use. edge-tts is MIT licensed.
