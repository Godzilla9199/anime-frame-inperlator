'''

Model 8:27 PM
Now I have the complete picture of your setup:
AI Agents: Gemini Pro (in Google AI Studio / Build App) + Qwen-Coder (local/agentic).
OS: Windows (so paths, .exe binaries, and subprocess calls must be 100% Windows-native).
RIFE 4.7 Installation: Automated self-bootstrapper (auto-downloads the official rife-ncnn-vulkan Windows binary + rife-v4.7 model directly into ./models/ if not already installed).
Drastic Change (24fps Action Scenes): Treat as animated on 1s (24fps) -> Generate 3x (24 * 3 = 72 FPS) via RIFE, and evenly drop the 12 extra generated frames per second (keeping 5 out of every 6 frames) to hit an exact, smooth 60 FPS—while only blocking true camera cuts (100% new scene) from morphing.
Telemetry & Tuning Log (debug_log.txt / .json): Instead of cluttering the video, generate a human-readable Debug Log File that records every single segment (Time X.XXs to Y.YYs | Frames X to Y), showing the active thresholds at the top and logging the exact Center Deflection, Global Deflection, Crop Box Coords, and the Decision (1s -> 3x (72fps decimated to 60fps), 2s -> 5x, 3s -> 8x decimated, 4s -> 10x, or Static Hold).
Below are your updated, finalized 3 Markdown files incorporating every single one of these Windows, 72->60fps decimation, and debug-file rules, followed by the Master Kickoff Prompt to paste into Gemini Pro / Qwen-Coder.
File 1: project.md
code
Markdown
# PROJECT DIRECTIVE: Windows Content-Aware Anime Frame Interpolator (24fps -> 60fps)

## 1. SYSTEM PERSONA & PRIME DIRECTIVE
You are a Principal Systems & Computer Vision Engineer targeting **Windows**. Your objective is to build a local, memory-efficient, sliding-window anime interpolation pipeline in Python.
**CRITICAL RULE:** Do NOT deviate from this architecture. Read `restrictions.md` and `implementation_plan.md` completely before writing code. When prompted, build modularly, do not omit implementation details with `# TODO`, and never forget the core math or thresholds defined here.

## 2. THE CORE GOAL
Anime is animated on variable intervals: 1s (24fps), 2s (12fps), 3s (8fps), or 4s (6fps), often mixing moving backgrounds (1s) with static center characters (2s/3s). Running RIFE blindly creates stutter because it interpolates between duplicate frames.
**Our Goal:** Produce a clean, artifact-free **60 FPS MP4 (H.264)** with **exact audio sync** by:
1. Extracting frames in **30-frame sliding windows** (to save disk/RAM).
2. Using a **Two-Pointer (`i`, `j`) algorithm** (looking ahead up to `j - i = 4`) to detect & delete duplicate frames.
3. Comparing both **Global Frame Deflection** and a **Resolution-Independent 50% Center-Crop Deflection**.
4. Using **RIFE 4.7 (`rife-ncnn-vulkan` on AMD iGPU)** to generate the exact multiple of frames needed for each segment, dropping excess generated frames to lock onto 60 FPS (`16.666ms` per frame).
5. Writing a detailed **`debug_decisions.log`** file so the user can easily inspect the deflection numbers for every timestamp/frame range and dial in the thresholds in `config.py`.

## 3. THE TWO-POINTER & DEFLECTION LOGIC

### A. 30-Frame Sliding Window & Two Pointers (`i` and `j`)
* Pointer `i` is the start keyframe. Pointer `j` (`j = i + 1`) scans forward up to `i + 4`.
* Compare Frame `i` with Frame `j`:
  * If they are duplicates (or fall under the minuscule background-only change rule), **delete/ignore the duplicate frame** and extend `j` (`j += 1`) until we hit a frame that is genuinely redrawn, or until `j - i > 4`.
  * **Why stop at 4?** Anime is drawn on 1s, 2s, 3s, or 4s. If a frame is constant for more than 4 frames (`j - i > 4`), it is a **Static Hold Frame**—do NOT touch/interpolate it with RIFE; simply duplicate it to match 60 FPS timing.

### B. Resolution-Independent 50% Center Crop & Deflection Rules
For any resolution ($W \times H$), compute the 50% center crop box:
* `x1 = int(W * 0.25)`, `x2 = int(W * 0.75)`
* `y1 = int(H * 0.25)`, `y2 = int(H * 0.75)`
Compute `center_deflection` (inside the box) and `global_deflection` (whole frame) between `i` and `j`:
1. **Exact Duplicate (`global_deflection <= THRESH_DUPLICATE`):** Frame `j` is identical to `i`. Delete `j` and extend pointer `j`.
2. **Minuscule Change / Moving Background + Static Subject (`center_deflection <= THRESH_CENTER_STATIC` and `global_deflection <= THRESH_MINUSCULE_CHANGE`):** The character in the center is static on 2s while the background pans slightly. Treat this pair as **drawn on 2s (12fps)**: drop the middle frame and let RIFE generate 5x (12fps -> 60fps). RIFE easily reconstructs minuscule background motion and eliminates 2s judder.
3. **Drastic Change / Action Scene (`global_deflection >= THRESH_DRASTIC_CHANGE`, up to `THRESH_CAMERA_CUT`):** Fast action animated on **1s (24fps)**. Do not drop frames; treat as 24fps and interpolate **3x (24fps -> 72fps)**, then **drop the 12 extra generated frames per second** (drop 1 generated frame out of every 6) to land smoothly on **60 FPS**.
4. **True Camera Cut (`global_deflection >= THRESH_CAMERA_CUT`):** A completely new shot/scene. Do not run RIFE between two unrelated scenes; pad with the original frame to maintain 60fps sync.

### C. Multiplier & Frame-Dropping Table (24 FPS Input -> 60 FPS Output)
At 24 FPS, 1 source frame = `41.666ms`. At 60 FPS, 1 output frame = `16.666ms`.
| Animation Cadence | Source Span ($j - i$) | Effective FPS | Time Span | RIFE Multiplier | Frame Decimation / Drop Rule | Final Output Frames |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1s (Drastic / Action)** | 1 frame | 24 FPS | `41.67ms` | **3x** (72 FPS) | Generate 3 frames per input frame (6 frames per 2 input frames), **drop 1 generated frame** out of every 6 (removes 12 fps from 72 fps) | **2.5 frames** avg (5 per 2 src frames) |
| **2s (Standard)** | 2 frames | 12 FPS | `83.33ms` | **5x** (60 FPS) | Exact match (`0ms`, `16.6ms`, `33.3ms`, `50.0ms`, `66.6ms`) | **5 frames** |
| **3s (Slow)** | 3 frames | 8 FPS | `125.00ms` | **8x** (64 FPS) | Generate 8 frames across gap; **drop 1 extra generated frame** on alternating 3s segments | **7.5 frames** avg (alternates 7 and 8) |
| **4s (Very Slow)** | 4 frames | 6 FPS | `166.67ms` | **10x** (60 FPS) | Exact match (10 frames at `16.66ms` steps across `166.67ms`) | **10 frames** |
| **Static (>4 frames)** | >4 frames | Static | $N \times 41.67\text{ms}$ | **None (0x)** | Duplicate source frame without calling RIFE | $N \times 2.5$ frames |
File 2: restrictions.md
code
Markdown
# HARDWARE, OS & ARCHITECTURAL RESTRICTIONS

Every module you write MUST obey these hard constraints. Do not violate them even after multiple prompts.

## 1. ENVIRONMENT & HARDWARE
* **OS:** Windows 10/11 (64-bit). All file paths must use `pathlib.Path` or `os.path.join` so Windows backslashes never cause escape bugs.
* **CPU / GPU:** AMD Processor with Integrated AMD Radeon iGPU.
* **RAM / Shared VRAM:** 16 GB total system RAM.
* **Target Performance:** 720p resolution (must work dynamically on any resolution, no hardcoded `1280x720` math), achieving 3–5 FPS through RIFE on Vulkan.

## 2. STRICT MODEL & BACKEND RULES
* **NO PYTORCH / NO CUDA:** Never `import torch`. AMD iGPUs on Windows must use **Vulkan (`ncnn`)**.
* **AUTO-INSTALL RIFE 4.7:** Your code must include an automated setup module (`src/setup_rife.py`) that checks if `./models/rife-v4.7` and `rife-ncnn-vulkan.exe` (or `rife-ncnn-vulkan-python`) exist. If not, it automatically downloads the official Windows `rife-ncnn-vulkan` release zip from GitHub (`nihui/rife-ncnn-vulkan`), extracts `rife-ncnn-vulkan.exe` and the `rife-v4.7` model folder into `./models/`, and verifies execution.
* **NO UPSCALING:** Strictly frame interpolation only. Input resolution == Output resolution.

## 3. STORAGE & MEMORY LIMITS
* **30-FRAME EXTRACTION LIMIT:** Never extract the entire video to disk. Extract and process at most **30 source frames** per batch in `./temp_buffer/`, and wipe the temp files after each batch is piped into the encoder.
* **OUTPUT FORMAT:** Standard `.mp4` using `libx264` (`-pix_fmt yuv420p -crf 18 -preset fast`) with the original audio track muxed back in with zero drift.

## 4. DEBUG LOG & TUNABILITY REQUIREMENT
* **EASY-TO-EDIT THRESHOLDS:** Every single threshold number must be at the top of `config.py` with clear explanations.
* **MANDATORY DEBUG LOG (`debug_telemetry.log`):** For every run, generate a clean, structured text log file that:
  1. Prints the current active thresholds and crop box dimensions at the very top of the file.
  2. Logs every segment with:
     `[Time: 00:01.000 -> 00:01.083 | Src Frames: 24 -> 26 (Span: 2)] CenterDeflection: 0.92 | GlobalDeflection: 3.41 | CropBox: (320,180)-(960,540) | Decision: ANIMATED_ON_2S (Minuscule BG Change) -> RIFE 5x (Generated 5 frames, Dropped 0)`
File 3: implementation_plan.md
code
Markdown
# IMPLEMENTATION PLAN & SUB-AGENT TASK BREAKDOWN

Build this project step-by-step according to the module specifications below. Do not skip any edge cases.

---

## TARGET PROJECT STRUCTURE
```text
project_root/
├── config.py                 # All user-editable thresholds, paths, and settings
├── main.py                   # CLI entry point (python main.py --input clip.mp4 --output out_60fps.mp4)
├── debug_telemetry.log       # Generated automatically on each run for threshold tuning
├── models/                   # Auto-downloaded rife-ncnn-vulkan.exe & rife-v4.7 model
├── temp_buffer/              # Wiped after every 30-frame chunk
└── src/
    ├── __init__.py
    ├── setup_rife.py         # Sub-Agent 1: Auto-downloader for Windows rife-ncnn-vulkan + rife-v4.7
    ├── video_io.py           # Sub-Agent 2: 30-frame chunk extractor & FFmpeg H.264 MP4 pipe writer
    ├── analyzer.py           # Sub-Agent 3: Two-pointer deduplicator, 50% Center-Crop & Debug Logger
    └── interpolator.py       # Sub-Agent 4: RIFE 4.7 runner, 72->60fps & 64->60fps frame dropper, sync clock
STEP-BY-STEP MODULE SPECIFICATIONS
MODULE 1: config.py (The Tuning Control Panel)
Must contain clearly commented constants so the user can tweak them in 5 seconds:
code
Python
from pathlib import Path

# ==============================================================================
# 1. FRAME DEFLECTION THRESHOLDS (Scale: 0.0 to 255.0 Mean Absolute Pixel Diff)
# ==============================================================================
# If Global Deflection between Frame i and Frame j is <= THRESH_DUPLICATE,
# Frame j is considered an identical duplicate and deleted.
THRESH_DUPLICATE = 0.85

# If the 50% Center Crop Deflection is <= THRESH_CENTER_STATIC, the main subject
# in the middle of the screen is considered NOT moving.
THRESH_CENTER_STATIC = 1.60

# When the center subject is static (<= THRESH_CENTER_STATIC) and the Global
# Deflection is <= THRESH_MINUSCULE_CHANGE, it means only the background is
# moving slightly. We treat this as 2s (12fps), delete the middle frame, and let RIFE 5x it.
THRESH_MINUSCULE_CHANGE = 6.50

# To prevent deleting tiny lip-sync mouth flaps inside a static center crop,
# if the 99th-percentile pixel diff inside the center crop exceeds this, treat as redrawn.
THRESH_LIP_SYNC_PEAK = 18.0

# If Global Deflection is >= THRESH_DRASTIC_CHANGE (and below THRESH_CAMERA_CUT),
# it is a fast action scene on 1s (24fps). We interpolate 3x (to 72fps) and drop 12fps -> 60fps.
THRESH_DRASTIC_CHANGE = 15.0

# If Global Deflection is >= THRESH_CAMERA_CUT, it is a hard scene change.
# Never interpolate across a camera cut (prevents morph artifacts).
THRESH_CAMERA_CUT = 48.0

# ==============================================================================
# 2. WINDOW, CROP & TIMING SETTINGS
# ==============================================================================
EXTRACTION_BATCH_SIZE = 30    # Extract max 30 frames at a time
MAX_J_LOOKAHEAD = 4           # Only expand pointer j up to 4 frames (1s, 2s, 3s, 4s)
CENTER_CROP_FACTOR = 0.50     # 50% zoom into the center (dynamic for any resolution)
TARGET_FPS = 60.0             # 16.666667 ms per frame

# ==============================================================================
# 3. WINDOWS PATHS & RIFE SETTINGS
# ==============================================================================
BASE_DIR = Path(__file__).parent.resolve()
MODELS_DIR = BASE_DIR / "models"
RIFE_EXE_PATH = MODELS_DIR / "rife-ncnn-vulkan.exe"
RIFE_MODEL_NAME = "rife-v4.7"
TEMP_DIR = BASE_DIR / "temp_buffer"
DEBUG_LOG_PATH = BASE_DIR / "debug_telemetry.log"
GPU_ID = 0                    # 0 = Primary AMD iGPU
MODULE 2: src/setup_rife.py (Sub-Agent 1: Zero-Friction RIFE 4.7 Installer)
Check if RIFE_EXE_PATH and MODELS_DIR / "rife-v4.7" exist.
If not, use urllib.request to query or download the official Windows binary release zip from https://github.com/nihui/rife-ncnn-vulkan/releases (and if the zip only has up to rife-v4.6, automatically fetch the rife-v4.7 .param and .bin weights from the official repo/mirror into models/rife-v4.7/).
Also verify ffmpeg is accessible on Windows PATH (or imageio_ffmpeg.get_ffmpeg_exe() as automatic fallback so the user never gets a FileNotFoundError on Windows).
MODULE 3: src/video_io.py (Sub-Agent 2: 30-Frame Streamer & H.264 Writer)
VideoChunkReader:
Opens the input .mp4 using cv2.VideoCapture.
Reads metadata: src_fps, width, height, total_frames.
Yields batches of at most EXTRACTION_BATCH_SIZE (30) frames, where each item is a FrameData(index, timestamp_ms, bgr_array).
FFmpegH264Writer:
Spawns a Windows-compatible subprocess.Popen running FFmpeg:
ffmpeg -y -f rawvideo -vcodec rawvideo -s {W}x{H} -pix_fmt bgr24 -r 60 -i - -c:v libx264 -pix_fmt yuv420p -crf 18 -preset fast temp_video_60fps.mp4
Provides write_frame(bgr_array) which pipes bgr_array.tobytes() directly into stdin.
Provides finalize_and_mux_audio(original_video_path, final_output_path) which closes stdin and runs FFmpeg to copy the 60fps video stream and mux the original audio stream (-c:v copy -c:a aac -b:a 192k -map 0:v:0 -map 1:a:0?).
'''