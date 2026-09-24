"""
Main execution pipeline:
- Prompts start ID and batch size immediately (Zero-wait CLI).
- Only processes and searches images for stories explicitly selected.
- Supports both loose IDs ('15') and padded IDs ('015').

Usage:
    python scripts/run_pipeline.py
    python scripts/run_pipeline.py --upload
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline_utils import (
    load_topics, save_status, step_done, load_step_module,
    print_summary
)

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    ("illustration", "01_fetch_illustration.py"),
    ("image_description", "02_inspect_image.py"),
    ("story", "03_generate_story.py"),
    ("clean", "04_clean_story.py"),
    ("audio", "05_generate_audio.py"),
    ("captions", "06_generate_captions.py"),
    ("video", "07_assemble_video.py"),
    ("metadata", "08_generate_metadata.py"),
]


def select_target_stories(all_rows):
    total = len(all_rows)
    all_ids = [str(r["id"]).strip() for r in all_rows]

    print("\n" + "=" * 65)
    print(f"🎬 FOLKTALE AUTOMATION PIPELINE (TỔNG CỘNG: {total} STORIES)")
    print(f"Dải ID hiện có: [{all_ids[0]}] ... [{all_ids[-1]}]")
    print("=" * 65)

    # Nhập ID bắt đầu (Chấp nhận cả '15' lẫn '015')
    raw_start = input(f">> Chạy từ Story ID nào? [Mặc định: {all_ids[0]}]: ").strip()
    
    target_idx = 0
    if raw_start:
        padded_start = raw_start.zfill(3) if raw_start.isdigit() else raw_start
        found = False
        for idx, sid in enumerate(all_ids):
            if sid == raw_start or sid == padded_start:
                target_idx = idx
                found = True
                break
            if sid.isdigit() and raw_start.isdigit() and int(sid) == int(raw_start):
                target_idx = idx
                found = True
                break
        if not found:
            print(f"⚠️ Không tìm thấy ID '{raw_start}'. Tự động bắt đầu từ ID đầu tiên ({all_ids[0]}).")

    available_queue = all_rows[target_idx:]

    # Nhập số lượng muốn tạo
    count_input = input(f">> Muốn tạo bao nhiêu video? [Enter để chạy hết {len(available_queue)} stories còn lại]: ").strip()
    if count_input.isdigit() and int(count_input) > 0:
        final_queue = available_queue[:int(count_input)]
    else:
        final_queue = available_queue

    # Tùy chọn dừng sau từng video
    step_by_step = input(">> Dừng hỏi xác nhận sau MỖI video hoàn tất? [y/N]: ").strip().lower() == "y"

    print("\n" + "-" * 65)
    print(f"📋 KẾ HOẠCH XỬ LÝ {len(final_queue)} STORY ĐƯỢC CHỌN:")
    for r in final_queue:
        print(f" - ID {str(r['id']).strip():<4}: {r['tale']}")
    print("-" * 65 + "\n")

    return final_queue, step_by_step


def process_story(row, modules, upload_module=None, youtube=None):
    story_id = str(row["id"]).strip()
    print(f"=======================================================")
    print(f"### Bắt đầu Story {story_id}: {row['tale']} ({row['variation_angle']}) ###")
    print(f"=======================================================")

    for step_name, module in modules:
        if step_done(story_id, step_name):
            print(f"  [{step_name}] đã hoàn thành trước đó, bỏ qua.")
            continue
        try:
            module.run(row)
            save_status(story_id, step_name, "done")
            print(f"  [{step_name}] hoàn tất.")
        except Exception as e:
            save_status(story_id, step_name, "failed", str(e))
            print(f"  [{step_name}] THẤT BẠI: {e}")
            print(f"  --> Dừng story {story_id} tại đây, chuyển sang story tiếp theo.\n")
            return False

    if upload_module is not None:
        if step_done(story_id, "upload"):
            print("  [upload] đã upload rồi, bỏ qua.")
        else:
            try:
                upload_module.run(row, youtube=youtube)
                save_status(story_id, "upload", "done")
                print("  [upload] hoàn tất.")
            except Exception as e:
                save_status(story_id, "upload", "failed", str(e))
                print(f"  [upload] THẤT BẠI: {e}")
                return False

    print(f"🎉 Hoàn thành video cho Story {story_id}!\n")
    return True


def main():
    modules = [(name, load_step_module(SCRIPTS_DIR, filename)) for name, filename in STEPS]

    upload_module = None
    youtube = None
    if "--upload" in sys.argv:
        upload_module = load_step_module(SCRIPTS_DIR, "09_upload_youtube.py")
        print("Đang xác thực YouTube...")
        youtube = upload_module.get_authenticated_service()

    all_rows = load_topics()
    if not all_rows:
        print("Lỗi: topics.csv trống hoặc không tìm thấy.")
        return

    # Vào menu chọn ngay lập tức, không ping tìm kiếm trước
    selected_rows, pause_between = select_target_stories(all_rows)
    if not selected_rows:
        return

    for idx, row in enumerate(selected_rows):
        process_story(row, modules, upload_module=upload_module, youtube=youtube)

        # Chế độ dừng hỏi nếu người dùng bật
        if pause_between and idx < len(selected_rows) - 1:
            next_id = str(selected_rows[idx + 1]["id"]).strip()
            user_choice = input(f"[?] Tiếp tục sang Story {next_id}? [Y/n/q]: ").strip().lower()
            if user_choice in ("n", "q", "exit"):
                print("Đã dừng pipeline theo lệnh người dùng.")
                break

    print_summary()


if __name__ == "__main__":
    main()