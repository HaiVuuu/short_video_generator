"""
Step 5: synthesize narration audio + word timing for ONE story.
Output: output/<id>/audio.mp3, output/<id>/word_boundaries.json
"""
import os
import sys
import json
import asyncio
import re
import edge_tts
from mutagen.mp3 import MP3  # Thư viện đọc thời lượng audio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TTS_VOICE, TTS_RATE
from pipeline_utils import load_topics, story_dir


def fallback_boundaries(text, audio_path):
    """
    Dự phòng: Nếu Edge-TTS không trả WordBoundary, tự tính timing dựa trên
    độ dài audio và tỷ lệ độ dài của từng từ trong câu chuyện.
    """
    try:
        audio = MP3(audio_path)
        total_duration = audio.info.length
    except Exception:
        # Dự đoán sơ bộ nếu chưa đọc được metadata MP3 (130 từ/phút)
        words_count = len(text.split())
        total_duration = (words_count / 130.0) * 60.0

    words = re.findall(r'\S+', text)
    if not words:
        return []

    # Tính trọng số theo độ dài ký tự của từng từ
    total_chars = sum(len(w) for w in words)
    boundaries = []
    current_time = 0.0

    for w in words:
        word_duration = (len(w) / total_chars) * total_duration
        boundaries.append({
            "text": w,
            "offset": round(current_time, 3),
            "duration": round(word_duration, 3),
        })
        current_time += word_duration

    return boundaries


async def synthesize(text, audio_path, boundaries_path):
    communicate = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE)
    boundaries = []

    with open(audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            chunk_type = str(chunk.get("type", ""))
            if chunk_type == "audio":
                audio_file.write(chunk["data"])
            elif chunk_type in ("WordBoundary", "word_boundary"):
                boundaries.append({
                    "text": chunk.get("text", ""),
                    "offset": chunk["offset"] / 10_000_000,
                    "duration": chunk["duration"] / 10_000_000,
                })

    # Nếu không bắt được event từ Edge-TTS -> kích hoạt Fallback
    if not boundaries:
        print("  [Notice] Server không trả WordBoundary -> Sử dụng thuật toán dự phòng tính timing.")
        boundaries = fallback_boundaries(text, audio_path)

    with open(boundaries_path, "w", encoding="utf-8") as f:
        json.dump(boundaries, f, ensure_ascii=False, indent=2)


def run(row):
    story_id = row["id"]
    out_dir = story_dir(story_id)
    clean_path = os.path.join(out_dir, "story_clean.txt")
    audio_path = os.path.join(out_dir, "audio.mp3")
    boundaries_path = os.path.join(out_dir, "word_boundaries.json")

    if not os.path.exists(clean_path):
        raise RuntimeError("story_clean.txt missing — step 4 hasn't completed for this story yet")

    # Chỉ skip nếu cả 2 file đều đã tồn tại và hợp lệ
    audio_ok = os.path.exists(audio_path) and os.path.getsize(audio_path) > 0
    json_ok = os.path.exists(boundaries_path) and os.path.getsize(boundaries_path) > 10

    if audio_ok and json_ok:
        return

    with open(clean_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        raise RuntimeError("story_clean.txt bị rỗng.")

    asyncio.run(synthesize(text, audio_path, boundaries_path))


def main():
    for row in load_topics():
        story_id = row["id"]
        try:
            run(row)
            print(f"[{story_id}] audio and timing ready")
        except Exception as e:
            print(f"[{story_id}] FAILED: {e}")


if __name__ == "__main__":
    main()