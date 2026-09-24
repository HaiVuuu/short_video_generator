import os
from dotenv import load_dotenv
from static_ffmpeg.run import get_or_fetch_platform_executables_else_raise

load_dotenv()

# ---------------------------------------------------------------------------
# API Keys & Credentials
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    print("[WARNING] GEMINI_API_KEY not in .env")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")
FALLBACK_IMAGE_DIR = os.path.join(ASSETS_DIR, "fallback")
CREDENTIALS_DIR = os.path.join(BASE_DIR, "credentials")
TOPICS_CSV = os.path.join(BASE_DIR, "topics.csv")

# ---------------------------------------------------------------------------
# Model Configuration (Gemini API)
# ---------------------------------------------------------------------------
GEMINI_MODEL_STORY = ""
GEMINI_MODEL_VISION = ""

# ---------------------------------------------------------------------------
# TTS (Edge-TTS) - Voice Tone & Prosody
# ---------------------------------------------------------------------------
TTS_VOICE = "en-GB-RyanNeural"    
TTS_RATE = ""            
TTS_PITCH = ""              

# ---------------------------------------------------------------------------
# Video & Subtitle Rendering (9:16 Shorts)
# ---------------------------------------------------------------------------
VIDEO_RESOLUTION = "1080x1920"    
VIDEO_FPS = 
ZOOM_SPEED = 

# Subtitles (Safe Margin)
FONT_SIZE =
SUBTITLE_MARGIN_V = 
SUBTITLE_MARGIN_LR =

# ffmpeg/ffprobe
FFMPEG_BIN, FFPROBE_BIN = get_or_fetch_platform_executables_else_raise()

# ---------------------------------------------------------------------------
# Wikimedia Commons Ingestion
# ---------------------------------------------------------------------------
XXXXXXX_API = ""
XXXXXXX_IMAGE_WIDTH = 
XXXXXXX_USER_AGENT = ""

