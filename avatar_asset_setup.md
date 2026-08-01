# Avatar Asset Setup (one-time)

The avatar portrait is a single static image, generated once and reused for every video. Do not regenerate it per video — a consistent face is what makes this a recognizable channel character.

This channel is fronted by a persistent persona, **Maddie Ross**, 19, a college junior — see `persona.md` for her full backstory, personality, and content pillars. Every visual choice below keeps her unambiguously in the 18-19 college-adult bracket (per platform policy on monetized/sponsored content and minors), never younger.

## Exact prompt to use

Use this prompt (from `persona.md`'s visual description) verbatim, or close to it, in whichever free tool you pick below:

```
19-year-old college woman, shoulder-length light brown hair with subtle face-framing layers and soft curtain bangs, warm brown eyes, glowing skin, light natural makeup, casual college-Gen-Z style (fitted crewneck or oversized hoodie in a neutral color, small gold stud earrings), bright confident engaging smile making direct eye contact with camera, front-facing, shoulders-up framing, sitting in a simple dorm/apartment-style room with a blurred desk-and-monitor background and a warm gold rim light accent, soft flattering ring-light style lighting, high detail photorealistic portrait, scroll-stopping social-media-influencer quality, looks clearly like an adult college student (not a teenager, not stylized as younger)
```

Generate a few variations and pick the one that most clearly reads as an adult college student with a consistent, recognizable face — this is the image that gets reused for every single video, so spend the extra few minutes picking the best one.

## Requirements for the portrait

- Front-facing, neutral or slight smile, well-lit, shoulders-up framing.
- Plain or simple background (easier for SadTalker to process).
- Square or portrait aspect ratio, at least 512x512, ideally 768x768 or larger.
- Save as `assets/avatar.png`.

## Free ways to generate one

Pick any one of these, all free:

1. **Bing Image Creator** (https://www.bing.com/images/create) - free with a Microsoft account, DALL-E 3 based. Use the exact prompt above.

2. **Leonardo.ai free tier** (https://leonardo.ai) - free daily credits, good photorealistic presets. Use the exact prompt above.

3. **Stable Diffusion via a free Hugging Face Space** - search "stable diffusion" on https://huggingface.co/spaces and use any free-to-run demo Space (e.g. SDXL demos). No local GPU needed.

4. **Stable Diffusion via a free Colab notebook** - several community notebooks exist; search "Stable Diffusion Colab free" if you want more control over the prompt/seed.

## After generating

1. Download the image.
2. Save it locally as `assets/avatar.png` in this project.
3. Also upload a copy to the Drive `AIAvatarsBot_Inbox` folder as `avatar.png` (the Colab notebook reads it from there) - see README.md for the Drive folder setup.

This is a one-time task. Re-do it only if you want to change the channel's on-screen persona.
