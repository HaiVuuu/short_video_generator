"""
Step 9: upload ONE finished video to YouTube via the official Data API.
Uploads default to "private" for manual review — see config.py.
Output: output/<id>/uploaded.json
"""
import os
import sys
import json

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    YOUTUBE_CLIENT_SECRETS_FILE, YOUTUBE_TOKEN_FILE,
    YOUTUBE_CATEGORY_ID, YOUTUBE_DEFAULT_PRIVACY,
)
from pipeline_utils import load_topics, story_dir

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_authenticated_service():
    creds = None
    if os.path.exists(YOUTUBE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(YOUTUBE_TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(YOUTUBE_CLIENT_SECRETS_FILE):
                raise RuntimeError(
                    f"Missing {YOUTUBE_CLIENT_SECRETS_FILE} — see README's YouTube upload setup section."
                )
            flow = InstalledAppFlow.from_client_secrets_file(YOUTUBE_CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(YOUTUBE_TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def run(row, youtube=None):
    story_id = row["id"]
    out_dir = story_dir(story_id)
    video_path = os.path.join(out_dir, "video.mp4")
    metadata_path = os.path.join(out_dir, "metadata.json")
    uploaded_path = os.path.join(out_dir, "uploaded.json")

    if not os.path.exists(video_path):
        raise RuntimeError("video.mp4 missing — step 7 hasn't completed for this story yet")
    if not os.path.exists(metadata_path):
        raise RuntimeError("metadata.json missing — step 8 hasn't completed for this story yet")
    if os.path.exists(uploaded_path):
        return

    if youtube is None:
        youtube = get_authenticated_service()

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    body = {
        "snippet": {
            "title": metadata["title"], "description": metadata["description"],
            "tags": metadata.get("tags", []), "categoryId": YOUTUBE_CATEGORY_ID,
        },
        "status": {"privacyStatus": YOUTUBE_DEFAULT_PRIVACY, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    with open(uploaded_path, "w", encoding="utf-8") as f:
        json.dump({"video_id": video_id, "url": f"https://youtube.com/watch?v={video_id}",
                    "privacy": YOUTUBE_DEFAULT_PRIVACY}, f, indent=2)


def main():
    youtube = get_authenticated_service()
    for row in load_topics():
        story_id = row["id"]
        try:
            run(row, youtube=youtube)
            print(f"[{story_id}] uploaded")
        except Exception as e:
            print(f"[{story_id}] FAILED: {e}")


if __name__ == "__main__":
    main()
