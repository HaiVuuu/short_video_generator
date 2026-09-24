import asyncio
import os
import edge_tts

# Đoạn trích thử nghiệm từ kịch bản Story 101
SAMPLE_TEXT = (
    "Two pale, frantic legs rupture the surface of the green sea, "
    "a final, graceless thrash before the abyss claims the boy. "
    "Pieter Bruegel the Elder ignores the spectacle, burying his brush in the mundane toil "
    "of a plowman's hunched spine. History is not a tragedy; it is a relentless, ticking machinery of apathy. "
    "Your extinction will not even pause the plow."
)

# Danh sách các cấu hình giọng trầm, phim tài liệu để nghe thử
CANDIDATES = [
    {
        "name": "01_US_Christopher_Deep",
        "voice": "en-US-ChristopherNeural",
        "rate": "-10%",
        "pitch": "-20Hz",
        "desc": "Nam Mỹ - Trầm ấm, phong cách phim tài liệu lịch sử"
    },
    {
        "name": "02_GB_Ryan_Macabre",
        "voice": "en-GB-RyanNeural",
        "rate": "-12%",
        "pitch": "-10Hz",
        "desc": "Nam Anh - Trầm gằn, quý tộc cổ điển, rất hợp tranh Phục Hưng"
    },
    {
        "name": "03_GB_Thomas_SlowDread",
        "voice": "en-GB-ThomasNeural",
        "rate": "-15%",
        "pitch": "-15Hz",
        "desc": "Nam Anh - Siêu trầm, chậm rãi, tạo không khí ma mị, lạnh lẽo"
    }
]

OUT_DIR = "test_audio_samples"
os.makedirs(OUT_DIR, exist_ok=True)

async def test_single(candidate):
    out_file = os.path.join(OUT_DIR, f"{candidate['name']}.mp3")
    print(f"[*] Đang render: {candidate['name']} ({candidate['desc']})...")
    comm = edge_tts.Communicate(
        text=SAMPLE_TEXT,
        voice=candidate["voice"],
        rate=candidate["rate"],
        pitch=candidate["pitch"]
    )
    await comm.save(out_file)
    print(f"    -> Đã tạo: {out_file}")

async def main():
    print("=== BẮT ĐẦU TẠO MẪU GIỌNG TTS THỬ NGHIỆM ===")
    for c in CANDIDATES:
        await test_single(c)
    print(f"\n[Hoàn tất!] Mở thư mục '{OUT_DIR}' để nghe thử 3 file mp3.")

if __name__ == "__main__":
    asyncio.run(main())