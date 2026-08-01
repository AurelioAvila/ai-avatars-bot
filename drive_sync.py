import argparse
import io
import time
from pathlib import Path

import yaml
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

CONFIG_PATH = Path(__file__).parent / "config.yaml"
CREDENTIALS_PATH = Path(__file__).parent / "credentials.json"
TOKEN_PATH = Path(__file__).parent / "token.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_drive_service():
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    "credentials.json not found. Follow the Google Drive API setup "
                    "steps in README.md before running drive_sync.py."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def find_or_create_folder(service, folder_name, parent_id=None):
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        metadata["parents"] = [parent_id]
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def upload_file(service, file_path, folder_id):
    file_path = Path(file_path)
    metadata = {"name": file_path.name, "parents": [folder_id]}
    media = MediaFileUpload(str(file_path), resumable=True)
    uploaded = service.files().create(body=metadata, media_body=media, fields="id, name").execute()
    return uploaded


def upload_to_inbox(audio_path, config):
    service = get_drive_service()
    inbox_name = config["paths"]["drive_inbox_folder_name"]
    folder_id = find_or_create_folder(service, inbox_name)
    uploaded = upload_file(service, audio_path, folder_id)
    print(f"Uploaded {uploaded['name']} to Drive inbox folder '{inbox_name}' (file id: {uploaded['id']})")
    return uploaded["id"]


def poll_outbox_for_video(video_id, config, timeout_seconds=1800, poll_interval_seconds=20):
    service = get_drive_service()
    outbox_name = config["paths"]["drive_outbox_folder_name"]
    folder_id = find_or_create_folder(service, outbox_name)

    expected_name_prefix = video_id
    elapsed = 0

    print(
        f"Polling Drive outbox folder '{outbox_name}' for a file starting with "
        f"'{expected_name_prefix}'. Run the Colab notebook (colab/avatar_lipsync.ipynb) "
        f"now if you have not already."
    )

    while elapsed < timeout_seconds:
        query = f"'{folder_id}' in parents and trashed=false and name contains '{expected_name_prefix}'"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get("files", [])
        if files:
            return files[0]
        time.sleep(poll_interval_seconds)
        elapsed += poll_interval_seconds

    raise TimeoutError(
        f"No rendered video found in Drive outbox after {timeout_seconds} seconds. "
        "Check that the Colab notebook ran successfully."
    )


def download_file(file_id, dest_path, config=None):
    service = get_drive_service() if config is None else get_drive_service()
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(dest_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.close()
    return dest_path


def main():
    parser = argparse.ArgumentParser(description="Upload TTS audio to Drive and poll for rendered avatar video.")
    parser.add_argument("action", choices=["upload", "poll"])
    parser.add_argument("--audio-path", help="Path to audio file (upload action)")
    parser.add_argument("--video-id", help="Video id to look for in outbox (poll action)")
    parser.add_argument("--dest", help="Destination path for the downloaded video (poll action)")
    args = parser.parse_args()

    config = load_config()

    if args.action == "upload":
        if not args.audio_path:
            raise SystemExit("--audio-path is required for upload")
        upload_to_inbox(args.audio_path, config)
    elif args.action == "poll":
        if not args.video_id or not args.dest:
            raise SystemExit("--video-id and --dest are required for poll")
        found = poll_outbox_for_video(args.video_id, config)
        download_file(found["id"], args.dest)
        print(f"Downloaded rendered avatar video to {args.dest}")


if __name__ == "__main__":
    main()
