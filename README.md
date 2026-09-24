# Multimodal Video Synthesis Pipeline (Image-Grounded Automation)

An end-to-end automated pipeline designed to synthesize cinematic vertical videos (9:16) from fine-art visual inputs. The system grounds storytelling in vision analysis, handles multi-frame visual sequencing with motion filtering, aligns audio narration via neural TTS, and manages automated platform delivery.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Ready-green.svg)](https://ffmpeg.org/)

---

## Architectural Highlights

Unlike conventional video pipelines that generate narrative and visuals disconnectedly, this pipeline employs an **Image-First Grounded Workflow**:
1. **Curated Visual Ingestion:** Resolves and queries high-resolution open-access museum archives and Wikimedia Commons repositories.
2. **Deep Vision Inspection:** Analyzes input artwork via Vision-Language Models (Google Gemini 2.0 / Multimodal LLMs) to extract compositional hierarchy, color balance, brushwork gestures, and subject anatomy.
3. **Grounded Narrative Generation:** Synthesizes pacing-controlled narration strictly locked to the inspected visual features, avoiding hallucination and generic descriptions.
4. **Cinematic Motion & Audio Engineering:** 
   - Uses an advanced FFmpeg filter-complex chain (`bicubic` zoom, RGBA transparent padding, and dynamic background blur) to completely eliminate 9:16 aspect ratio letterboxing and frame jitter.
   - Dynamic ambient audio layering with automatic intro timestamp offsets and crossfading audio ducking.
5. **Word-Level Subtitle Alignment:** Synchronizes burn-in subtitles styled for modern mobile safe zones using neural speech timestamps.

---

## Project Structure

```text
├── assets/
│   └── music/                # Ambient tracks for background audio mixing
├── prompts/                  # System & structural instruction prompts
├── scripts/
│   ├── pipeline_utils.py     # State management, topic parsing, status caching
│   ├── 01_fetch_assets.py    # Multi-frame image acquisition & metadata extraction
│   ├── 02_inspect_image.py   # Vision API inspection & spatial analysis
│   ├── 03_generate_story.py  # Grounded narrative synthesis
│   ├── 04_generate_tts.py    # Neural TTS rendering (low-frequency pitch adjusted)
│   ├── 05_sync_captions.py   # Forced alignment subtitle generation (SRT)
│   ├── 06_assemble_video.py  # Multi-shot FFmpeg filter pipeline (Blur + Motion + BGM)
│   ├── 07_gen_metadata.py    # SEO tagging & platform upload payload
│   └── run_pipeline.py       # Fault-tolerant batch runner with per-item isolation
├── config.example.py         # Environmental template
├── requirements.txt          # Python dependencies
└── status.json               # Auto-generated execution audit logs

##Core Technologies

Vision & LLM: Google Gemini 2.0 Flash (google-genai SDK) / Multimodal LLM endpoints.

Audio Processing: Edge Neural TTS & ElevenLabs API; Dynamic Audio Mixing via FFmpeg amix & afade.

Media Engine: FFmpeg & FFprobe (Custom complex filter chains for 9:16 motion interpolation).

Automation: Python 3.10+, Batch Processing with isolated state recovery (status.json).

Quickstart
###1. Prerequisites
Python 3.10+

FFmpeg installed and added to your system PATH:
```
# Windows (via Chocolatey)
choco install ffmpeg
# macOS (via Homebrew)
brew install ffmpeg
# Linux (Ubuntu/Debian)
sudo apt install ffmpeg
```
###2. Environment Setup
```
# Clone the repository
git clone [https://github.com/HaiVuuu/short_video_generator.git](https://github.com/HaiVuuu/short_video_generator.git)
cd short_video_generator

# Initialize virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

###3. Configuration
Copy the configuration template:
```
cp config.example.py config.py
```
Edit config.py with your credentials:
```
GEMINI_API_KEY = "your_gemini_api_key"
VIDEO_RESOLUTION = "1080x1920"
VIDEO_FPS = 30
```
###4. Running the Pipeline
Run the full pipeline sequentially:
```
python scripts/run_pipeline.py
```

To run individual steps in isolation:
```
# Example: Inspect imagery
python scripts/02_inspect_image.py

# Example: Assemble video from existing assets
python scripts/06_assemble_video.py
```
Technical FeaturesFrame Jitter Elimination on 9:16 Aspect RatiosWhen placing landscape artwork onto a vertical $1080 \times 1920$ canvas, dynamic scaling often causes subpixel jitter due to odd coordinate rounding. This pipeline solves the issue by enforcing an RGBA alpha-channel canvas pad:
```
[0:v]scale=1080:-2:force_original_aspect_ratio=decrease,format=rgba,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x00000000[fg_canvas]
```

This locks coordinates to an exact matrix, enabling smooth Ken-Burns zooms over blurred backgrounds without frame degradation.

License
This project is licensed under the MIT License - see the LICENSE file for details.
