"""
Step 1: Multi-image interactive selector.
Allows selecting 1 or more images/crops for a story to form a visual storyboard.
Output: output/<id>/illustration_0.jpg, illustration_1.jpg... and attribution.json
"""
import os
import sys
import json
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import WIKIMEDIA_IMAGE_WIDTH
from pipeline_utils import (
    load_topics, story_dir, fetch_artwork_candidates, HEADERS
)


def download(url, dest_path):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    with open(dest_path, "wb") as f:
        f.write(r.content)


def run(row):
    story_id = str(row["id"]).strip()
    tale = row["tale"].strip()
    out_dir = story_dir(story_id)
    attribution_path = os.path.join(out_dir, "attribution.json")

    # Kiểm tra nếu đã có ít nhất 1 ảnh và attribution
    if os.path.exists(os.path.join(out_dir, "illustration_0.jpg")) and os.path.exists(attribution_path):
        return

    # Lấy tối đa 8 ứng viên (gồm cả toàn cảnh và các bản chi tiết nếu có)
    candidates = fetch_artwork_candidates(row, max_candidates=8, image_width=WIKIMEDIA_IMAGE_WIDTH)
    if not candidates:
        raise RuntimeError(f"[{story_id}] Không tìm thấy tác phẩm minh họa nào trên Commons.")

    print(f"\n🎨 Tìm thấy {len(candidates)} tác phẩm/chi tiết cho Story {story_id} ({tale}):")
    print("-" * 75)
    for i, c in enumerate(candidates, 1):
        print(f"[{i}] Tiêu đề : {c['title'][:45]}")
        print(f"    Bố cục  : {c['orientation']} ({c['dimensions']})")
        print(f"    Link    : {c['page_url']}")
        print("-" * 75)

    # Hỏi người dùng chọn bao nhiêu ảnh
    num_input = input(f">> Muốn dùng bao nhiêu ảnh cho video này? [1-3, Mặc định: 1]: ").strip()
    num_images = int(num_input) if num_input.isdigit() and 1 <= int(num_input) <= 3 else 1

    selected_list = []
    for idx in range(num_images):
        prompt_txt = f">> Chọn ảnh thứ {idx+1}/{num_images} [1-{len(candidates)}, Mặc định: {idx+1}]: "
        pick = input(prompt_txt).strip()
        choice_idx = int(pick) - 1 if pick.isdigit() and 1 <= int(pick) <= len(candidates) else idx
        selected_list.append(candidates[min(choice_idx, len(candidates) - 1)])

    os.makedirs(out_dir, exist_ok=True)
    
    # Lưu các file ảnh theo thứ tự storyboard
    for idx, item in enumerate(selected_list):
        dest = os.path.join(out_dir, f"illustration_{idx}.jpg")
        download(item["url"], dest)
        if idx == 0:
            # Lưu thêm 1 bản copy illustration.jpg để tương thích ngược
            download(item["url"], os.path.join(out_dir, "illustration.jpg"))

    # Lưu metadata của tất cả các ảnh đã chọn
    with open(attribution_path, "w", encoding="utf-8") as f:
        json.dump(selected_list, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã lưu {num_images} phân cảnh cho Story {story_id}.")


def main():
    for row in load_topics():
        try:
            run(row)
        except Exception as e:
            print(f"[{row['id']}] FAILED: {e}")


if __name__ == "__main__":
    main()