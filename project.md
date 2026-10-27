# PROJECT DIRECTIVE: Dynamic Content-Aware Anime Frame Interpolator (24fps -> 60fps)

## 1. SYSTEM PERSONA & PRIME DIRECTIVE
You are an expert Systems & Computer Vision Engineer. Your sole objective is to build a local, memory-efficient, sliding-window video interpolation pipeline in Python. 
**CRITICAL RULE:** Do NOT deviate from this architecture. Do NOT hallucinate features (no 4K upscaling, no web UIs, no PyTorch/CUDA dependencies). Read `restrictions.md` and `implementation_plan.md` before writing a single line of code. Always expose threshold variables at the top of a `config.py` file for easy user tuning.

## 2. THE CORE PROBLEM & GOAL
Standard frame interpolation (running RIFE blindly on a 24fps anime) fails because anime is drawn on variable intervals: 1s (24fps), 2s (12fps), 3s (8fps), or 4s (6fps). Blind interpolation interpolates between identical duplicate frames, causing a "stutter-smooth-stutter" artifact (the soap-opera effect on steroids) and fails on panning shots where the background moves on 1s while the character in the center is drawn on 2s or 3s.

**Our Goal:** Achieve a buttery-smooth, artifact-free **60 FPS** output (16.666ms per frame) with **perfect audio synchronization** by dynamically deduplicating frames using a Two-Pointer sliding window, analyzing center-crop motion vs. global motion, and instructing the `rife-ncnn-vulkan` (RIFE v4.7) backend to generate the exact number of intermediate frames needed for that specific time delta.

## 3. CORE ALGORITHMIC PILLARS

### A. Sliding Window Extraction (30-Frame Buffer)
* Never extract the whole video at once. Process the video in chunks of **30 frames** (at 24fps, 1 frame = `41.666ms`).
* Maintain a rolling carryover buffer for frames at the end of the 30-frame window whose duplicate sequence hasn't resolved yet.

### B. Two-Pointer Deduplication (`i` and `j`)
* Pointer `i` is the anchor frame. Pointer `j` scans ahead (`j = i + 1`).
* Expand `j` forward as long as Frame `i` and Frame `j` are deemed "identical" (based on our multi-zone heuristics) **up to a maximum step limit of 4** (`j - i <= 4`).
* **Why max 4?** Anime is drawn on 1s, 2s, 3s, or 4s. If `j - i > 4` (e.g., 5+ identical frames), it is a deliberately paused/static hold frame. **Do not interpolate static holds**—simply duplicate them to match the 60fps timeline.
* Delete the intermediate duplicate frames between `i` and `j`, keeping only the unique keyframes and their original timestamps.

### C. Resolution-Independent Center-Crop & Motion Heuristics
To solve the "moving background (on 1s) + static character (on 2s/3s)" problem:
1. Dynamically calculate a **50% Center Crop** bounding box regardless of whether the video is 720p, 1080p, etc.:
   * `x_start = int(W * 0.25)`, `x_end = int(W * 0.75)`
   * `y_start = int(H * 0.25)`, `y_end = int(H * 0.75)`
2. Compute difference metrics (MSE / SSIM / Mean Absolute Diff) between Frame `i` and Frame `j` for both the **Center Crop** and the **Outer Background**.
3. **Decision Matrix (All thresholds must be tunable in `config.py`):**
   * **Case 1: Exact Duplicate (` diff < THRESH_IDENTICAL `):** Drop Frame `j`, advance `j`.
   * **Case 2: Minuscule Change / Panning Shot (Center is static `< THRESH_CENTER_STATIC`, Background moves `< THRESH_MINOR_MOTION`):** Treat as animated on 2s (12fps). Drop the middle frame so RIFE interpolates smoothly across the 2-frame gap, reconstructing both the background pan and any micro-shifts cleanly to 60fps.
   * **Case 3: Moderate Change (Standard animation):** Use the detected gap (`1s`, `2s`, `3s`, or `4s`) to interpolate via RIFE.
   * **Case 4: Drastic Change / Scene Cut (`diff > THRESH_SCENE_CUT`):** Do **NOT** interpolate. RIFE will create disgusting morphing artifacts on scene cuts or extreme action smears. Treat as 24fps (or duplicate original frames to fill the 60fps time slot without calling RIFE).

### D. Time-Delta Math & RIFE Multiplier Mapping (Target = 60 FPS / 16.666ms)
At 24 FPS input, each source step $N = (j - i)$ spans $N \times 41.666\text{ms}$. To reach 60 FPS ($16.666\text{ms}$ per frame):
* **Animated on 1s ($N=1$, 24fps, span = $41.67\text{ms}$):** Target needs $2.5$ frames per source frame. Generate **5x** (or 4x/2x via RIFE) across pairs and decimate/resample timestamps to exact $16.666\text{ms}$ intervals.
* **Animated on 2s ($N=2$, 12fps, span = $83.33\text{ms}$):** $83.33 / 16.666 = 5$. We need **5x generation** (1 start frame + 4 RIFE generated frames = 5 frames total before Frame `j`).
* **Animated on 3s ($N=3$, 8fps, span = $125.00\text{ms}$):** $125.00 / 16.666 = 7.5$. RIFE cannot generate $7.5$ frames. Instruct RIFE to generate **8x** (producing 8 frames across the gap), then **drop 1 extra generated frame** on alternating 3s chunks (7 frames, then 8 frames = $7.5$ average) to keep strict $16.666\text{ms}$ alignment.
* **Animated on 4s ($N=4$, 6fps, span = $166.67\text{ms}$):** $166.67 / 16.666 = 10$. Instruct RIFE to generate **10x** (or generate 16x/8x and decimate to exactly 10 frames across the $166.67\text{ms}$ gap).

### E. Audio Alignment
The final assembled 60 FPS video stream must match the exact duration of the source video down to the millisecond, and the original audio stream must be muxed back in seamlessly without drift.