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
UNIVERSAL_VISION_PROMPT = """Analyze this illustration frame with objective, museum-grade visual accuracy:
- Primary Subjects & Anatomy: Identify all distinct figures, entities, or prominent anatomical elements visible in this frame (e.g. human postures, creatures, exposed limbs, silhouettes).
- Physical Actions & Interactions: Describe what each figure is physically doing, holding, or looking at. Note any tools, weapons, garments, or contact between objects. If none, state 'isolated'.
- Environment & Spatial Setting: Describe the immediate setting (indoor chamber, body of water, cliff, forest, open sky), ground plane, and lighting condition.

Strict Rules:
- Return strictly 3 concise, factual bullet points corresponding to the 3 categories above.
- Record ONLY what is visually rendered in the brushwork/linework.
- Do NOT guess identities, allegories, or story titles.
- Do NOT invent objects or animals that are not explicitly delineated."""


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
    # Bạn có thể đổi sang 'gemini-2.0-flash-lite' hoặc 'gemini-2.5-flash' tùy nhu cầu thử nghiệm
    active_model = "gemini-3.1-flash-lite"

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