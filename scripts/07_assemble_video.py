"""
Step 7: Robust Multi-Image Video Assembly.
Renders each visual shot cleanly into individual segments, then concats with audio and burns subtitles.
Zero filter-complex conflicts, guaranteed no Error -22.
Output: output/<id>/video.mp4
"""
import os
import sys
import glob
import subprocess
import ctypes
from ctypes import wintypes

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    VIDEO_RESOLUTION, VIDEO_FPS, ZOOM_SPEED,
    FFMPEG_BIN, FFPROBE_BIN
)
from pipeline_utils import load_topics, story_dir


def get_short_path_name(long_name):
    if sys.platform != "win32":
        return long_name
    _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
    _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    _GetShortPathNameW.restype = wintypes.DWORD
    buf_size = 0
    while True:
        buf = ctypes.create_unicode_buffer(buf_size)
        needed = _GetShortPathNameW(long_name, buf, buf_size)
        if buf_size >= needed:
            return buf.value
        buf_size = needed


def get_audio_duration(audio_path):
    r = subprocess.run(
        [
            FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", audio_path
        ],
        capture_output=True, text=True, check=True
    )
    return float(r.stdout.strip())


def get_image_size(image_path):
    try:
        r = subprocess.run(
            [
                FFPROBE_BIN, "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=s=x:p=0", image_path
            ],
            capture_output=True, text=True, check=True
        )
        w, h = r.stdout.strip().split("x")
        return int(w), int(h)
    except Exception:
        return 1080, 1920


def render_single_shot(img_path, out_clip_path, duration, target_w, target_h):
    """
    Render 1 bức ảnh thành clip 9:16 chuẩn:
    - Có nền mờ cinematic (KHÔNG còn viền đen).
    - Khử rung giật 100% bằng cách pad kênh RGBA trong suốt và overlay cố định 0:0.
    """
    img_w, img_h = get_image_size(img_path)
    total_frames = int(round(duration * VIDEO_FPS))
    is_landscape = img_w > img_h

    if is_landscape:
        # 1. Background: scale lấp đầy, làm mờ, hạ sáng
        # 2. Foreground: format=rgba để hỗ trợ alpha, pad trong suốt thành 1080x1920, 
        #    sau đó zoom toàn khung hình từ tâm bằng bicubic (không tính lại overlay)
        filter_str = (
            f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
            f"crop={target_w}:{target_h},boxblur=30:5,eq=brightness=-0.2,"
            f"fps={VIDEO_FPS},trim=duration={duration}[bg];"
            f"[0:v]scale={target_w}:-2:force_original_aspect_ratio=decrease,"
            f"format=rgba,"
            f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:color=0x00000000[fg_canvas];"
            f"[fg_canvas]scale=w='{target_w}*(1+0.05*n/{total_frames})':h='{target_h}*(1+0.05*n/{total_frames})':"
            f"flags=bicubic+accurate_rnd:eval=frame,"
            f"crop={target_w}:{target_h}:'(in_w-{target_w})/2':'(in_h-{target_h})/2'[fg_zoom];"
            f"[bg][fg_zoom]overlay=0:0:eval=init[v]"
        )
    else:
        # Ảnh đứng (Portrait): Zoom nhẹ mượt mà từ tâm
        filter_str = (
            f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
            f"crop={target_w}:{target_h},"
            f"scale=w='{target_w}*(1+0.06*n/{total_frames})':h='{target_h}*(1+0.06*n/{total_frames})':"
            f"flags=bicubic+accurate_rnd:eval=frame,"
            f"crop={target_w}:{target_h}:'(in_w-{target_w})/2':'(in_h-{target_h})/2',"
            f"fps={VIDEO_FPS},trim=duration={duration}[v]"
        )

    cmd = [
        FFMPEG_BIN, "-y",
        "-loop", "1", "-i", img_path,
        "-filter_complex", filter_str,
        "-map", "[v]",
        "-t", str(duration),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
        out_clip_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Shot render failed for {img_path}: {res.stderr[-500:]}")

def run(row):
    story_id = str(row["id"]).strip()
    out_dir = os.path.abspath(story_dir(story_id))
    audio_path = os.path.join(out_dir, "audio.mp3")
    srt_path = os.path.join(out_dir, "captions.srt")
    final_video_path = os.path.join(out_dir, "video.mp4")

    if not os.path.exists(audio_path):
        raise RuntimeError(f"[{story_id}] audio.mp3 missing")
    if not os.path.exists(srt_path):
        raise RuntimeError(f"[{story_id}] captions.srt missing")

    # Lấy danh sách ảnh
    image_paths = sorted(glob.glob(os.path.join(out_dir, "illustration_[0-9]*.jpg")))
    if not image_paths:
        fallback = os.path.join(out_dir, "illustration.jpg")
        if os.path.exists(fallback):
            image_paths = [fallback]
        else:
            raise RuntimeError(f"[{story_id}] No illustration files found.")

    if os.path.exists(final_video_path) and os.path.getsize(final_video_path) > 1024:
        return

    duration = get_audio_duration(audio_path)
    target_w, target_h = [int(x) for x in VIDEO_RESOLUTION.split("x")]
    shot_duration = duration / len(image_paths)

    # 1. Render từng shot hình độc lập
    shot_files = []
    for idx, img_path in enumerate(image_paths):
        shot_clip = os.path.join(out_dir, f"temp_shot_{idx}.mp4")
        print(f"  [video] Đang xử lý phân cảnh {idx+1}/{len(image_paths)}...")
        render_single_shot(img_path, shot_clip, shot_duration, target_w, target_h)
        shot_files.append(shot_clip)

    # 2. Tạo file danh sách nối clips
    concat_list_path = os.path.join(out_dir, "concat_list.txt")
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for clip in shot_files:
            # Đường dẫn tuyệt đối chuẩn hóa cho file concat của ffmpeg
            f.write(f"file '{clip.replace(os.sep, '/')}'\n")

    # 3. Chuẩn bị phụ đề
    short_srt = get_short_path_name(srt_path)
    ffmpeg_srt_arg = short_srt.replace("\\", "/").replace(":", r"\:")

    subtitle_style = (
        "PlayResX=1080,PlayResY=1920,"
        "FontName=Impact,FontSize=68,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,Outline=4.2,Shadow=2,"
        "Alignment=2,"
        "MarginV=420,"
        "MarginL=60,MarginR=60"
    )

    # 4. Ghép nối clips + nạp Audio + dập Subtitles trong 1 lệnh duy nhất
    print("  [video] Đang ghép nối phân cảnh và dập phụ đề...")
    cmd_final = [
        FFMPEG_BIN, "-y",
        "-f", "concat", "-safe", "0", "-i", concat_list_path,
        "-i", audio_path,
        "-vf", f"subtitles='{ffmpeg_srt_arg}':force_style='{subtitle_style}'",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration), "-shortest",
        final_video_path
    ]

    res = subprocess.run(cmd_final, capture_output=True, text=True)

    # 5. Dọn dẹp các file tạm
    for clip in shot_files:
        if os.path.exists(clip):
            try:
                os.remove(clip)
            except Exception:
                pass
    if os.path.exists(concat_list_path):
        try:
            os.remove(concat_list_path)
        except Exception:
            pass

    if res.returncode != 0:
        raise RuntimeError(f"Final assembly failed: {res.stderr[-600:]}")


def main():
    for row in load_topics():
        story_id = row["id"]
        try:
            run(row)
            print(f"[{story_id}] Multi-frame video ready")
        except Exception as e:
            print(f"[{story_id}] FAILED: {e}")


if __name__ == "__main__":
    main()