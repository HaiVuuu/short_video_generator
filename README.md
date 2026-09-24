# Folk Tale Retelling Pipeline

**Image-first flow**: pulls a public-domain illustration, has a vision
model describe what's actually in it, then has your text model write a
retelling grounded in that description — so the narration matches the
picture on screen, instead of a story and an image being generated
independently and hoping they line up.

Processes **one story fully through every step before starting the
next**, with per-story error isolation: if one story fails at any step
(a bad image search, an Ollama hiccup, whatever), that story stops there
and the pipeline moves on to the next one rather than crashing the whole
batch. Every story's progress is tracked in its own `status.json`, and a
summary prints at the end showing exactly what succeeded, what failed,
and why.

## Folder structure

```
folktale_pipeline/
├── config.py
├── topics.csv                     # tale + culture + variation angle + optional image overrides
├── requirements.txt
├── setup.sh / setup.bat           # one-time venv setup
├── prompts/
│   └── story_prompt.txt           # now includes the image description as grounding
├── assets/
│   ├── fallback/                  # backup illustrations if Commons search finds nothing
│   └── manual/                    # exact images you want to use — see image_file below
├── credentials/
│   ├── client_secret.json         # you add this — see YouTube upload setup
│   └── token.json                 # auto-created after first login
├── scripts/
│   ├── pipeline_utils.py          # shared status tracking / topic loading
│   ├── 01_fetch_illustration.py   # pulls the image — runs FIRST now
│   ├── 02_inspect_image.py        # NEW — vision model describes the image
│   ├── 03_generate_story.py       # writes the story, grounded in that description
│   ├── 04_clean_story.py
│   ├── 05_generate_audio.py
│   ├── 06_generate_captions.py
│   ├── 07_assemble_video.py
│   ├── 08_generate_metadata.py
│   ├── 09_upload_youtube.py
│   └── run_pipeline.py            # orchestrator — one story at a time
└── output/
    └── 001/
        ├── illustration.jpg           (step 1)
        ├── attribution.json           (step 1 — real artist/credit when Commons has it)
        ├── image_description.txt      (step 2 — what the vision model saw, storyteller-oriented)
        ├── story.txt                  (step 3 — opens with an artwork intro, then the retelling)
        ├── meta_input.json            (step 3)
        ├── story_clean.txt            (step 4)
        ├── audio.mp3                  (step 5)
        ├── word_boundaries.json       (step 5)
        ├── captions.srt               (step 6)
        ├── video.mp4                  (step 7 — final output)
        ├── metadata.json              (step 8 — description includes an artwork credit line)
        ├── uploaded.json              (step 9, if --upload used)
        └── status.json                ← per-step pass/fail record for this story
```

## One-time setup

1. **Ollama** — pull TWO models, a text model and a vision model:
   ```
   ollama pull llama3.1:8b
   ollama pull llava:7b
   ```
   Make sure Ollama is actually running before you generate anything:
   `ollama serve` (or it may already run as a background service).

2. **ffmpeg** — must be on your PATH (`brew install ffmpeg` / `choco install ffmpeg` / `apt install ffmpeg`)

3. **Python deps**, isolated in a virtual environment:
   - macOS/Linux: `bash setup.sh`
   - Windows: `setup.bat`

   Then either call the venv's Python directly:
   ```
   ./venv/bin/python scripts/run_pipeline.py        # macOS/Linux
   venv\Scripts\python scripts\run_pipeline.py       # Windows
   ```
   or activate it once per terminal session and use `python` normally:
   ```
   source venv/bin/activate      # macOS/Linux
   venv\Scripts\activate         # Windows
   ```

4. **Fallback images**: drop a few public-domain illustrations into
   `assets/fallback/` in case a Commons search comes up empty.

## Controlling which image gets used

You're not stuck with whatever the automatic Commons search happens to
find. Two optional columns in `topics.csv`, per row:

- **`image_file`** — an exact filename you've placed in `assets/manual/`.
  If set, this is used as-is and the Commons search is skipped entirely.
  Use this whenever you already know which piece of art you want.
- **`image_query`** — a custom Wikimedia Commons search string, replacing
  the auto-built `"<tale> <illustrator_style> illustration"` query. Use
  this when the auto-query isn't finding the right kind of image but you
  still want it pulled from Commons rather than supplying your own file.

Leave both blank to use the default auto-search behavior.

## Running it

Generate videos only (no upload):
```
python scripts/run_pipeline.py
```

Generate AND upload to YouTube:
```
python scripts/run_pipeline.py --upload
```

Each story prints its own progress as it goes:
```
### Story 003: The Snow Maiden (the Slavic folk variant...) ###
  [illustration] done
  [image_description] done
  [story] done
  [clean] done
  [audio] done
  [captions] done
  [video] done
  [metadata] done
```
If something fails partway, you'll see exactly where and why, and the
run continues to the next story instead of stopping:
```
### Story 004: Vasilisa the Beautiful (...) ###
  [illustration] FAILED: No image found on Commons and no fallback images...
  Stopping this story here — moving on to the next one.
```

At the end, a summary shows every story's outcome in one place:
```
============================================================
PIPELINE SUMMARY
============================================================
[001] OK — video ready (not uploaded)
[002] OK — video ready (not uploaded)
[003] OK — uploaded
[004] FAILED
    at 'illustration': No image found on Commons and no fallback images...
============================================================
```

**Re-running is always safe.** Every step checks whether its output
already exists and skips it if so — fix whatever caused story 004 to
fail (add a fallback image, set `image_file` for that row, etc.) and
re-run `run_pipeline.py`; stories 001-003 won't be redone, and 004 will
pick up right where it left off.

You can also run any single step standalone across all topics, useful
for debugging one stage in isolation:
```
python scripts/02_inspect_image.py
```

## Troubleshooting

**`404 Client Error: Not Found for url: http://localhost:11434/api/generate`**
This means Ollama doesn't have the model you asked for. Check `config.py`
for which model name is set (`OLLAMA_MODEL` or `OLLAMA_VISION_MODEL`) and
pull it: `ollama pull <model-name>`. The pipeline now catches this and
prints a specific message telling you exactly which model to pull.

**Ollama connection refused / "could not reach Ollama"**
Ollama isn't running. Start it with `ollama serve`.

**`[WinError 2] The system cannot find the file specified` (or "No such
file or directory" on Mac/Linux) at the `video` step**
This means ffmpeg (or ffprobe) isn't on your system PATH — nothing to do
with Wikimedia or the network. Either install ffmpeg properly and make
sure it's on PATH, or set `FFMPEG_BIN`/`FFPROBE_BIN` in `config.py` to
the full path of the executables, e.g.
`FFMPEG_BIN = r"C:\ffmpeg\bin\ffmpeg.exe"` on Windows.

**Commons search failing / getting blocked**
Wikimedia requires a descriptive `User-Agent` header on every API
request — the pipeline now sends one (`WIKIMEDIA_USER_AGENT` in
`config.py`). Put your own contact info in there; a generic or missing
User-Agent is exactly what gets rate-limited or blocked.

**A story keeps failing at `illustration`**
Either Commons genuinely has nothing for that search, or your network
call is failing. Set `image_file` for that row to a manually-sourced
image, or add more variety to `assets/fallback/`.

## YouTube upload setup

1. Go to console.cloud.google.com and create a project.
2. Enable the **YouTube Data API v3** (APIs & Services → Library).
3. Configure the OAuth consent screen → **External** → add your own
   Google account as a **test user** (no app review needed for personal use).
4. Create credentials → OAuth client ID → **Desktop app** → download the JSON.
5. Save it as `credentials/client_secret.json`.
6. First upload run opens a browser once for consent; after that,
   `credentials/token.json` is reused automatically.

Quota: ~6 uploads/day on Google's default free quota (10,000 units/day,
~1,600 units per upload) — plenty for a daily-upload schedule.

Uploads default to `privacyStatus: "private"` (`YOUTUBE_DEFAULT_PRIVACY`
in `config.py`) so nothing goes live without your review.

## Other ways to publish, if you don't want the API route

- **Fully manual**: take `output/<id>/video.mp4` + `metadata.json` and
  upload through YouTube Studio yourself.
- **TikTok / Instagram Reels**: both have official posting APIs but
  require business-account verification/app review before publishing
  live content — manual upload with the generated files as your caption
  source is the pragmatic path until you've set that up.
- **Scheduling**: once you trust the pipeline, add
  `python scripts/run_pipeline.py --upload` to cron (macOS/Linux) or
  Task Scheduler (Windows). Keep `YOUTUBE_DEFAULT_PRIVACY = "private"`
  even in a scheduled run.

## About topics.csv

Ships with 50 tales across French, German, Danish, Russian, Scandinavian,
Middle Eastern, Japanese, Chinese, Indian, Celtic, Greek, and English
traditions — enough for months of daily uploads without repeating a tale
or angle.

A couple of traditions were left out deliberately rather than included
carelessly: oral traditions from cultures without a large body of
public-domain illustrated adaptations (many West African, Native
American, and Aboriginal Australian tales, for example) deserve more
care than an automated "search Commons and hope" pipeline can give
them — both because usable public-domain illustrations are genuinely
harder to source, and because misrepresenting a living culture's oral
tradition is a different risk than retelling a 19th-century European
fairy tale. If you want to include these, source illustrations and frame
the text with a subject-matter source or consultant rather than relying
on the automated pipeline alone.

## Tuning

- **Voice**: `TTS_VOICE` in `config.py` — list all voices with `edge-tts --list-voices`.
- **Creativity**: `OLLAMA_STORY_TEMPERATURE` in `config.py` (0.7-0.9 typical for fiction).
- **Vision model**: `OLLAMA_VISION_MODEL` in `config.py` — `llava:7b` is
  the default; `llama3.2-vision:11b` is stronger but heavier;
  `moondream` is lighter/faster if hardware is tight.
- **Zoom speed / video length**: `ZOOM_SPEED`, `VIDEO_RESOLUTION`, `VIDEO_FPS` in `config.py`.
- **Retelling style**: edit `prompts/story_prompt.txt` — highest-leverage
  file for output quality; it now includes `{image_description}` as a
  placeholder, so any edits here should keep that grounding intact.
