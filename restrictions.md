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