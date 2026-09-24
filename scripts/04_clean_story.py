"""
Step 4: clean up raw story text for ONE story.
Output: output/<id>/story_clean.txt
NOTE: mechanical cleanup only — skim the text yourself before continuing.
"""
import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline_utils import load_topics, story_dir


def clean_text(text):
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"^#.*$", "", text, flags=re.M)
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def run(row):
    story_id = row["id"]
    out_dir = story_dir(story_id)
    story_path = os.path.join(out_dir, "story.txt")
    clean_path = os.path.join(out_dir, "story_clean.txt")

    if not os.path.exists(story_path):
        raise RuntimeError("story.txt missing — step 3 hasn't completed for this story yet")
    if os.path.exists(clean_path):
        return

    with open(story_path, "r", encoding="utf-8") as f:
        raw = f.read()

    with open(clean_path, "w", encoding="utf-8") as f:
        f.write(clean_text(raw))


def main():
    for row in load_topics():
        story_id = row["id"]
        try:
            run(row)
            print(f"[{story_id}] cleaned (review before continuing)")
        except Exception as e:
            print(f"[{story_id}] FAILED: {e}")


if __name__ == "__main__":
    main()
