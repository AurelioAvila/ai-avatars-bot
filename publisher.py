"""
Publishes a finished video (output/final/<id>.mp4 + _metadata.json) to
YouTube Shorts, Instagram Reels, and TikTok - same proven patterns already
used across the other 5 accounts this project manages (getcertsprint,
pctweaker10, groomlyco, magdock_4, solo_founded), not new ad-hoc code:

- YouTube: Data API v3, OAuth refresh-token flow (googleapiclient), same as
  every other YouTube Shorts channel here.
- Instagram: "Instagram API with Instagram Login" (graph.instagram.com,
  Bearer auth, IGAA-prefixed tokens) - NOT the classic Facebook Page-linked
  flow, which hit an unresolvable "linking isn't available" error on every
  account tried that way. Needs a public video_url, so the rendered mp4 is
  hosted as a temporary GitHub Release asset first (see github_asset_host.py
  in certsprint-reels-bot/solofounded-bot).
- TikTok: Content Posting API, uploads to the creator's TikTok inbox as a
  draft ("Upload to TikTok") rather than direct publish, since this app
  hasn't passed TikTok's "Direct Post" audit yet - same accepted workaround
  used for Groomlyco/Magdock.

One-time setup required before this actually works (none of it done yet -
this is a brand-new persona/channel, unlike the other 5 accounts which
already existed): create real YouTube/Instagram/TikTok accounts for Maddie
Ross, then generate credentials exactly like every other account's SETUP.md
walks through. Env vars expected:

  MADDIE_YOUTUBE_CLIENT_ID / _CLIENT_SECRET / _REFRESH_TOKEN
  MADDIE_IG_ACCESS_TOKEN / MADDIE_IG_USER_ID
  MADDIE_ASSETS_REPO_TOKEN / MADDIE_ASSETS_REPO   (GitHub PAT + "owner/repo"
                                                    for temporary video hosting)
  MADDIE_TIKTOK_CLIENT_KEY / _CLIENT_SECRET / _REFRESH_TOKEN

Until those exist, publish_all() raises a clear error per-platform instead
of failing silently, and always leaves the video in output/final/ for
manual upload as a fallback.
"""
import json
import os
import time
from pathlib import Path

import requests

YT_API_BASE = "https://www.googleapis.com/upload/youtube/v3/videos"
IG_API_BASE = "https://graph.instagram.com/v21.0"
TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"
GITHUB_API_BASE = "https://api.github.com"
GITHUB_UPLOAD_BASE = "https://uploads.github.com"


def _notify_telegram(video_path: str, caption: str) -> None:
    """Manda la caption pronta su Telegram appena il video finisce in bozza -
    l'endpoint bozze non la accetta via API, quindi senza questo bisognerebbe
    andarla a cercare a mano sul PC mentre si pubblica dal telefono. Stesso
    schema gia' usato per gli altri 5 account, numerazione progressiva propria
    (Maddie) cosi' non si mischia con gli altri contatori."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    counter_path = Path(__file__).parent / "output" / "telegram_notify_counter.json"
    n = 0
    if counter_path.exists():
        n = json.loads(counter_path.read_text()).get("n", 0)
    n += 1
    counter_path.write_text(json.dumps({"n": n}))

    video_name = os.path.basename(video_path)
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": f"🎬 Maddie #{n} — {video_name}"},
            timeout=15,
        )
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": caption},
            timeout=15,
        )
    except Exception as exc:
        print(f"[WARN] Notifica Telegram fallita per {video_name}: {exc}")


def _require_env(*names):
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise RuntimeError(
            f"Variabili d'ambiente mancanti: {', '.join(missing)}. "
            "Vedi il docstring in cima a publisher.py per la lista completa "
            "e SETUP.md (da creare, stesso schema degli altri account) per come generarle."
        )


# ---------------------------------------------------------------------------
# GitHub Release asset hosting (per il video_url pubblico richiesto da Instagram)
# ---------------------------------------------------------------------------

def _host_video_temporarily(video_path: str) -> tuple:
    _require_env("MADDIE_ASSETS_REPO_TOKEN", "MADDIE_ASSETS_REPO")
    repo = os.environ["MADDIE_ASSETS_REPO"]
    headers = {
        "Authorization": f"Bearer {os.environ['MADDIE_ASSETS_REPO_TOKEN']}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    tag = f"maddie-{int(time.time())}"

    create_resp = requests.post(
        f"{GITHUB_API_BASE}/repos/{repo}/releases",
        headers=headers,
        json={"tag_name": tag, "name": tag, "draft": False, "prerelease": False},
        timeout=30,
    )
    create_resp.raise_for_status()
    release_id = create_resp.json()["id"]

    filename = os.path.basename(video_path)
    with open(video_path, "rb") as f:
        video_bytes = f.read()

    upload_resp = requests.post(
        f"{GITHUB_UPLOAD_BASE}/repos/{repo}/releases/{release_id}/assets",
        headers={**headers, "Content-Type": "video/mp4"},
        params={"name": filename},
        data=video_bytes,
        timeout=120,
    )
    upload_resp.raise_for_status()
    return upload_resp.json()["browser_download_url"], release_id


def _delete_hosted_video(release_id) -> None:
    repo = os.environ["MADDIE_ASSETS_REPO"]
    headers = {"Authorization": f"Bearer {os.environ['MADDIE_ASSETS_REPO_TOKEN']}"}
    try:
        requests.delete(f"{GITHUB_API_BASE}/repos/{repo}/releases/{release_id}", headers=headers, timeout=30)
    except Exception as e:
        print(f"  [WARN] cleanup release fallito (non bloccante): {e}")


# ---------------------------------------------------------------------------
# YouTube Shorts
# ---------------------------------------------------------------------------

def publish_youtube(video_path: str, title: str, description: str, tags: list) -> str:
    _require_env("MADDIE_YOUTUBE_CLIENT_ID", "MADDIE_YOUTUBE_CLIENT_SECRET", "MADDIE_YOUTUBE_REFRESH_TOKEN")
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = Credentials(
        None,
        refresh_token=os.environ["MADDIE_YOUTUBE_REFRESH_TOKEN"],
        client_id=os.environ["MADDIE_YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["MADDIE_YOUTUBE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {"title": title[:100], "description": description[:5000], "tags": tags, "categoryId": "22"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = request.next_chunk()
    video_id = response["id"]
    print(f"[OK] YouTube pubblicato: video_id={video_id}")
    return video_id


# ---------------------------------------------------------------------------
# Instagram Reels
# ---------------------------------------------------------------------------

def publish_instagram(video_path: str, caption: str) -> str:
    _require_env("MADDIE_IG_ACCESS_TOKEN", "MADDIE_IG_USER_ID")
    access_token = os.environ["MADDIE_IG_ACCESS_TOKEN"]
    ig_user_id = os.environ["MADDIE_IG_USER_ID"]
    headers = {"Authorization": f"Bearer {access_token}"}

    video_url, release_id = _host_video_temporarily(video_path)
    try:
        create_resp = requests.post(
            f"{IG_API_BASE}/{ig_user_id}/media",
            headers=headers,
            data={"media_type": "REELS", "video_url": video_url, "caption": caption},
            timeout=30,
        )
        create_resp.raise_for_status()
        creation_id = create_resp.json()["id"]

        deadline = time.time() + 300
        status = "IN_PROGRESS"
        while time.time() < deadline and status not in ("FINISHED", "ERROR"):
            time.sleep(10)
            poll_resp = requests.get(
                f"{IG_API_BASE}/{creation_id}", headers=headers, params={"fields": "status_code"}, timeout=30
            )
            poll_resp.raise_for_status()
            status = poll_resp.json().get("status_code")

        if status != "FINISHED":
            raise RuntimeError(f"Instagram non ha elaborato il video (stato: {status})")

        publish_resp = requests.post(
            f"{IG_API_BASE}/{ig_user_id}/media_publish", headers=headers, data={"creation_id": creation_id}, timeout=30
        )
        publish_resp.raise_for_status()
        media_id = publish_resp.json()["id"]
        print(f"[OK] Instagram pubblicato: media_id={media_id}")
        return media_id
    finally:
        _delete_hosted_video(release_id)


# ---------------------------------------------------------------------------
# TikTok (inbox draft, in attesa dell'audit Direct Post)
# ---------------------------------------------------------------------------

def _tiktok_access_token() -> str:
    _require_env("MADDIE_TIKTOK_CLIENT_KEY", "MADDIE_TIKTOK_CLIENT_SECRET", "MADDIE_TIKTOK_REFRESH_TOKEN")
    resp = requests.post(
        f"{TIKTOK_API_BASE}/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": os.environ["MADDIE_TIKTOK_CLIENT_KEY"],
            "client_secret": os.environ["MADDIE_TIKTOK_CLIENT_SECRET"],
            "grant_type": "refresh_token",
            "refresh_token": os.environ["MADDIE_TIKTOK_REFRESH_TOKEN"],
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def publish_tiktok(video_path: str, caption: str) -> str:
    access_token = _tiktok_access_token()
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json; charset=UTF-8"}

    file_size = os.path.getsize(video_path)
    init_resp = requests.post(
        f"{TIKTOK_API_BASE}/post/publish/inbox/video/init/",
        headers=headers,
        json={"source_info": {"source": "FILE_UPLOAD", "video_size": file_size, "chunk_size": file_size, "total_chunk_count": 1}},
        timeout=30,
    )
    init_resp.raise_for_status()
    data = init_resp.json()["data"]
    publish_id, upload_url = data["publish_id"], data["upload_url"]

    with open(video_path, "rb") as f:
        video_bytes = f.read()
    requests.put(
        upload_url,
        headers={"Content-Type": "video/mp4", "Content-Range": f"bytes 0-{file_size - 1}/{file_size}"},
        data=video_bytes,
        timeout=120,
    ).raise_for_status()

    print(f"[OK] TikTok inviato nelle bozze: publish_id={publish_id}")
    _notify_telegram(video_path, caption)
    return publish_id


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def publish(video_path, metadata_path, skip_youtube=False, skip_instagram=False, skip_tiktok=False) -> dict:
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    caption = metadata["caption"] + "\n\n" + " ".join(f"#{h}" for h in metadata["hashtags"])
    results = {}

    if not skip_youtube:
        try:
            results["youtube_id"] = publish_youtube(video_path, metadata["title"], caption, metadata["hashtags"])
        except Exception as exc:
            print(f"  ! YouTube fallito: {exc}")
            results["youtube_error"] = str(exc)

    if not skip_instagram:
        try:
            results["instagram_media_id"] = publish_instagram(video_path, caption)
        except Exception as exc:
            print(f"  ! Instagram fallito: {exc}")
            results["instagram_error"] = str(exc)

    if not skip_tiktok:
        try:
            results["tiktok_publish_id"] = publish_tiktok(video_path, caption)
        except Exception as exc:
            print(f"  ! TikTok fallito: {exc}")
            results["tiktok_error"] = str(exc)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pubblica un video gia' assemblato su YouTube/Instagram/TikTok.")
    parser.add_argument("video_path")
    parser.add_argument("metadata_path")
    parser.add_argument("--skip-youtube", action="store_true")
    parser.add_argument("--skip-instagram", action="store_true")
    parser.add_argument("--skip-tiktok", action="store_true")
    args = parser.parse_args()

    outcome = publish(
        args.video_path, args.metadata_path,
        skip_youtube=args.skip_youtube, skip_instagram=args.skip_instagram, skip_tiktok=args.skip_tiktok,
    )
    print(json.dumps(outcome, indent=2))
