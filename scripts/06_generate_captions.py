"""
Step 6: build SRT captions from word timing data for ONE story.
Output: output/<id>/captions.srt
"""
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline_utils import load_topics, story_dir

WORDS_PER_CAPTION = 6


def format_timestamp(seconds):
    ms = int((seconds - int(seconds)) * 1000)
    s = int(seconds) % 60
    m = (int(seconds) // 60) % 60
    h = int(seconds) // 3600
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def build_srt(boundaries):
    lines = []
    idx = 1
    for i in range(0, len(boundaries), WORDS_PER_CAPTION):
        chunk = boundaries[i:i + WORDS_PER_CAPTION]
        start = chunk[0]["offset"]
        end = chunk[-1]["offset"] + chunk[-1]["duration"]
        text = " ".join(w["text"] for w in chunk)
        lines += [str(idx), f"{format_timestamp(start)} --> {format_timestamp(end)}", text, ""]
        idx += 1
    return "\n".join(lines)


def run(row):
    story_id = row["id"]
    out_dir = story_dir(story_id)
    boundaries_path = os.path.join(out_dir, "word_boundaries.json")
    srt_path = os.path.join(out_dir, "captions.srt")

    if not os.path.exists(boundaries_path):
        raise RuntimeError("word_boundaries.json missing — step 5 hasn't completed for this story yet")
    if os.path.exists(srt_path):
        return

    with open(boundaries_path, "r", encoding="utf-8") as f:
        boundaries = json.load(f)

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(build_srt(boundaries))


def main():
    for row in load_topics():
        story_id = row["id"]
        try:
            run(row)
            print(f"[{story_id}] captions ready")
        except Exception as e:
            print(f"[{story_id}] FAILED: {e}")


if __name__ == "__main__":
    main()
