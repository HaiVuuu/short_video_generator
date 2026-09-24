import os
import os
from dotenv import load_dotenv

# Tải toàn bộ biến môi trường từ file .env
load_dotenv()

# Lấy giá trị biến môi trường
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY chưa được thiết lập trong file .env")
# ---------------------------------------------------------------------------
# LLM (Ollama) — used for story generation AND metadata generation
# ---------------------------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"      # pull first: ollama pull llama3.1:8b

# Temperature controls randomness/creativity. Higher = more varied and
# surprising, lower = more predictable and literal.
OLLAMA_STORY_TEMPERATURE = 0.85     # 0.7-0.9 is the usual sweet spot for fiction
OLLAMA_METADATA_TEMPERATURE = 0.4   # keep titles/tags more consistent and on-format
OLLAMA_VISION_TEMPERATURE = 0.3     # keep image descriptions factual, not embellished

# ---------------------------------------------------------------------------
# Vision model — used ONLY to inspect the pulled illustration and describe
# what's actually in it, so the story generated afterward is grounded in
# the real image instead of guessing. A separate, smaller model than your
# main text model is normal here — vision models are a different job.
# ---------------------------------------------------------------------------
OLLAMA_VISION_MODEL = "llava:7b"   # pull first: ollama pull llava:7b
                                    # heavier/better option: llama3.2-vision:11b
                                    # lighter/faster option: moondream

# ---------------------------------------------------------------------------
# TTS (edge-tts)
# ---------------------------------------------------------------------------
TTS_VOICE = "en-GB-RyanNeural"   # pick one and keep it consistent — it's your brand's voice
TTS_RATE = "+0%"

# ---------------------------------------------------------------------------
# Illustration sourcing (Wikimedia Commons — public domain art, cleared rights)
# ---------------------------------------------------------------------------
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
WIKIMEDIA_IMAGE_WIDTH = 1600
FALLBACK_IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fallback")

# Wikimedia requires a descriptive User-Agent identifying your app/contact —
# requests without one get rate-limited or blocked. Replace the email below
# with your own; it doesn't need to be monitored, it just needs to exist.
# See: https://meta.wikimedia.org/wiki/User-Agent_policy
WIKIMEDIA_USER_AGENT = "FolktalePipeline/1.0 (personal project; contact: youremail@example.com)"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TOPICS_CSV = os.path.join(BASE_DIR, "topics_single.csv")
CREDENTIALS_DIR = os.path.join(BASE_DIR, "credentials")

# ---------------------------------------------------------------------------
# Video (Ken Burns pan/zoom over a still illustration)
# ---------------------------------------------------------------------------
VIDEO_RESOLUTION = "1080x1920"   # Vertical 9:16
VIDEO_FPS = 25
ZOOM_SPEED = 0.0006
TTS_RATE = "-12%"
TTS_PITCH = "-10Hz"  # Làm giọng trầm và dày hơn
# Cấu hình lại kích cỡ font và lề chuẩn YouTube Shorts
FONT_SIZE = 22                   # Giảm từ 60 xuống 22 để chữ vừa vặn khung hình
SUBTITLE_MARGIN_V = 280          # Đẩy chữ lên cách đáy 280px (tránh bị tiêu đề/nút Shorts che)
SUBTITLE_MARGIN_LR = 80
# ffmpeg/ffprobe executables. "ffmpeg"/"ffprobe" work if they're on your
# system PATH. If you get "[WinError 2] The system cannot find the file
# specified" (Windows) or "No such file or directory" (Mac/Linux), ffmpeg
# isn't on PATH — either fix your PATH, or point these at the full .exe
# path directly, e.g. r"C:\ffmpeg\bin\ffmpeg.exe"
from static_ffmpeg.run import get_or_fetch_platform_executables_else_raise

# Tự động định vị và cấp quyền đường dẫn ffmpeg/ffprobe trong venv
FFMPEG_BIN, FFPROBE_BIN = get_or_fetch_platform_executables_else_raise()
# ---------------------------------------------------------------------------
# YouTube upload (YouTube Data API v3)
# ---------------------------------------------------------------------------
YOUTUBE_CLIENT_SECRETS_FILE = os.path.join(CREDENTIALS_DIR, "client_secret.json")
YOUTUBE_TOKEN_FILE = os.path.join(CREDENTIALS_DIR, "token.json")
YOUTUBE_CATEGORY_ID = "24"        # "Entertainment" — see README for other IDs
YOUTUBE_DEFAULT_PRIVACY = "private"  # "private" | "unlisted" | "public"
                                      # keep "private" until you've reviewed a video yourself
