"""
Step 2: Universal, High-Precision Visual Inspection via Google GenAI SDK.
- Model: gemini-2.0-flash (fast, highly accurate, stable multimodal inference).
- Universal Prompt: Entity-agnostic, zero-bias across all art styles (European, Asian, Folklore).
Output: output/<id>/image_description.txt
"""
import os
import sys
import glob
from PIL import Image
from google import genai

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GEMINI_API_KEY
from pipeline_utils import load_topics, story_dir

client = genai.Client(api_key=GEMINI_API_KEY)

# Prompt phổ quát (Universal) - dùng cho mọi nền văn hóa, mọi thể loại tranh
UNIVERSAL_VISION_PROMPT = """     """


def describe_single_frame(image_path, model_name="gemini-2.0-flash"):
    img = Image.open(image_path)
    response = client.models.generate_content(
        model=model_name,
        contents=[img, UNIVERSAL_VISION_PROMPT]
    )
    return response.text.strip()


def run(row):
    story_id = str(row["id"]).strip()
    out_dir = story_dir(story_id)
    description_path = os.path.join(out_dir, "image_description.txt")

    img_patterns = sorted(glob.glob(os.path.join(out_dir, "illustration_[0-9]*.jpg")))
    if not img_patterns:
        fallback = os.path.join(out_dir, "illustration.jpg")
        if os.path.exists(fallback):
            img_patterns = [fallback]
        else:
            raise RuntimeError(f"[{story_id}] No illustration files found.")

    # Cho phép ghi đè nếu muốn phân tích lại với prompt phổ quát mới
    if os.path.exists(description_path) and os.path.getsize(description_path) > 0:
        with open(description_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "alligator" not in content.lower() and len(content.strip()) > 30:
            return

    descriptions = []
    
    active_model = "    "

    for idx, img_path in enumerate(img_patterns):
        print(f"  [vision-api] Phân tích góc máy {idx+1}/{len(img_patterns)} ({os.path.basename(img_path)}) bằng {active_model}...")
        desc = describe_single_frame(img_path, model_name=active_model)
        descriptions.append(f"Visual Frame {idx+1}:\n{desc}")

    full_description = "\n\n".join(descriptions)
    with open(description_path, "w", encoding="utf-8") as f:
        f.write(full_description)


def main():
    for row in load_topics():
        story_id = row["id"]
        try:
            run(row)
            print(f"[{story_id}] Universal visual inspection completed")
        except Exception as e:
            print(f"[{story_id}] FAILED: {e}")


if __name__ == "__main__":
    main()
