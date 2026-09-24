"""
Step 3: High-Quality Psychological Narration Generation via Gemini API.
Uses gemini-2.0-flash with dynamic hooks to prevent repetitive storytelling.
Output: output/<id>/story.txt
"""
import os
import sys
import re
from google import genai
from google.genai import types

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GEMINI_API_KEY
from pipeline_utils import load_topics, story_dir

client = genai.Client(api_key=GEMINI_API_KEY)

STORY_SYSTEM_PROMPT = """You are an elite dark folklore storyteller and art historian writing narration scripts for cinematic YouTube Shorts.
Your tone is psychological, cold, atmospheric, and deeply dramatic.
You ground every sentence in the physical brushwork, anatomy, and horrified expressions of the artwork."""

STORY_USER_PROMPT_TEMPLATE = """Context:
- Artwork: {artwork_title}
- Artist: {artist}
- Myth/Lore Tale: {tale}
- Narrative Angle: {variation_angle}
- Observed Visual Inspection Details:
{image_description}

Task: Write a strictly 115 to 130-word narration script for a YouTube Short. Follow this structure:
1. THE UNCONVENTIONAL HOOK (1 sentence): 
   - Plunge directly into the most harrowing action, visceral terror, or physical wound in the scene.
   - Weave {artist} and {tale} into the panic organically.
   - NEVER use clichés like 'In this chilling work...' or 'stripped of its romantic veneer'.
2. VISUAL GROUNDING (1-2 sentences): Anchor the viewer's eyes onto specific physical details from the Observed Visual Inspection (e.g. blood, tangled carpets, dilated pupils, limp limbs).
3. THE PSYCHOLOGICAL ABYSS (2 sentences): Unpack the irreversible tragedy and dread according to the Narrative Angle.
4. FINAL COLD VERDICT (1 sentence): A devastating realization about guilt, time, or mortality that lingers after the video ends.

CONSTRAINTS:
- No meta-words (DO NOT say 'this painting', 'we see', 'the frame shows').
- Output ONLY the spoken narration text. No titles, no notes.
- Word count: strictly 115 - 130 words."""


def run(row):
    story_id = str(row["id"]).strip()
    out_dir = story_dir(story_id)
    desc_path = os.path.join(out_dir, "image_description.txt")
    story_path = os.path.join(out_dir, "story.txt")

    if not os.path.exists(desc_path):
        raise RuntimeError(f"[{story_id}] image_description.txt missing")

    if os.path.exists(story_path) and os.path.getsize(story_path) > 50:
        return

    with open(desc_path, "r", encoding="utf-8") as f:
        image_desc = f.read().strip()

    # Dọn dẹp các từ ảo giác nếu có
    clean_desc = re.sub(r'\balligator\b', 'drowning figure', image_desc, flags=re.IGNORECASE)

    prompt = STORY_USER_PROMPT_TEMPLATE.format(
        artwork_title=row.get("image_query", row["tale"]),
        artist=row.get("illustrator_style", "Unknown Master"),
        tale=row["tale"],
        variation_angle=row["variation_angle"],
        image_description=clean_desc
    )

    config = types.GenerateContentConfig(
        system_instruction=STORY_SYSTEM_PROMPT,
        temperature=0.75,
        max_output_tokens=300
    )

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
        config=config
    )

    story_text = response.text.strip()
    # Loại bỏ ngoặc kép bao quanh nếu có
    story_text = re.sub(r'^["\']|["\']$', '', story_text)

    with open(story_path, "w", encoding="utf-8") as f:
        f.write(story_text)


def main():
    for row in load_topics():
        story_id = row["id"]
        try:
            run(row)
            print(f"[{story_id}] Story generated via Gemini API")
        except Exception as e:
            print(f"[{story_id}] FAILED: {e}")


if __name__ == "__main__":
    main()