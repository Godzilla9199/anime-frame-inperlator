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