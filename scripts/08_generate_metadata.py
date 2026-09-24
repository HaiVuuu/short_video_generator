"""
Step 8: Generate YouTube metadata (Title, Description, Tags)
Compatible with both single dict and multi-image list attribution schemas.
Output: output/<id>/metadata.json
"""
import os
import sys
import json
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_METADATA_TEMPERATURE
from pipeline_utils import load_topics, story_dir

METADATA_SYSTEM_PROMPT = """You are a YouTube SEO expert specializing in dark folklore, art history, and mythology Shorts.
You output strictly valid JSON with no markdown wrapping or preamble."""

METADATA_USER_TEMPLATE = """Story ID: {id}
Tale: {tale}
Culture: {culture}
Artist: {artist}
Artwork: {artwork_title}
Script:
{story}

Generate a JSON object with:
- "title": A punchy, cinematic YouTube Shorts title (under 50 chars, high CTR, no clickbait quotes).
- "description": 2-3 sentences explaining the artwork's hidden meaning, followed by attribution: "Artwork: {artist} ({artwork_url})".
- "tags": Array of 8-12 relevant lowercase tags (mythology, art history, folklore, specific entities).

Output ONLY valid raw JSON."""

def run(row):
    story_id = str(row["id"]).strip()
    out_dir = story_dir(story_id)
    story_path = os.path.join(out_dir, "story.txt")
    attr_path = os.path.join(out_dir, "attribution.json")
    meta_path = os.path.join(out_dir, "metadata.json")

    if not os.path.exists(story_path):
        raise RuntimeError(f"[{story_id}] story.txt missing")

    # Đọc attribution an toàn cho cả list và dict
    attr_data = {}
    if os.path.exists(attr_path):
        with open(attr_path, "r", encoding="utf-8") as f:
            raw_attr = json.load(f)
            if isinstance(raw_attr, list) and len(raw_attr) > 0:
                attr_data = raw_attr[0]
            elif isinstance(raw_attr, dict):
                attr_data = raw_attr

    artist = attr_data.get("artist") or row.get("illustrator_style", "Pieter Bruegel the Elder")
    artwork_title = attr_data.get("title") or row["tale"]
    artwork_url = attr_data.get("page_url", "https://commons.wikimedia.org")

    with open(story_path, "r", encoding="utf-8") as f:
        story_text = f.read().strip()

    prompt = METADATA_USER_TEMPLATE.format(
        id=story_id,
        tale=row["tale"],
        culture=row["culture"],
        artist=artist,
        artwork_title=artwork_title,
        artwork_url=artwork_url,
        story=story_text
    )

    payload = {
        "model": OLLAMA_MODEL,
        "system": METADATA_SYSTEM_PROMPT,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": OLLAMA_METADATA_TEMPERATURE}
    }

    res = requests.post(OLLAMA_URL, json=payload, timeout=120)
    res.raise_for_status()
    metadata_json = res.json()["response"].strip()

    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(metadata_json)

def main():
    for row in load_topics():
        try:
            run(row)
            print(f"[{row['id']}] metadata generated")
        except Exception as e:
            print(f"[{row['id']}] METADATA FAILED: {e}")

if __name__ == "__main__":
    main()