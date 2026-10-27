'''
MODULE 5: src/interpolator.py (Sub-Agent 4: RIFE 4.7 Engine & Frame Decimation)
Exact 60 FPS Timing & Drift-Free Accumulator:
Maintain src_clock_ms and out_clock_ms (where each output frame advances out_clock_ms by 1000.0 / 60.0 = 16.666667ms).
For any segment of span source frames (span in 1..4), the segment end time is src_clock_ms += span * (1000.0 / src_fps).
Exact number of 60fps frames needed for this segment:
needed_60fps_frames = int(round((src_clock_ms - out_clock_ms) / 16.666667))
out_clock_ms += needed_60fps_frames * 16.666667
RIFE Generation & Frame-Dropping Logic:
Case A (STATIC_HOLD or CAMERA_CUT_PAD):
Output frame_i repeated needed_60fps_frames times. (0 RIFE calls).
Case B (DRASTIC_1S_72TO60 or INTERPOLATE_1S — 24fps to 60fps via 72fps):
Instruct RIFE 4.7 to generate 3x between frame_i and frame_j (which produces 3 frames per 1 source frame = 72 FPS: [F_i, Gen_1, Gen_2]).
Across pairs of 1s frames (6 frames at 72fps = 83.33ms), we need needed_60fps_frames (which alternates between 2 and 3 frames per single 1s step, equaling 5 frames per two 1s steps = 60 FPS).
Drop the extra generated frame on the 2-frame step (keeping [F_i, Gen_1] or [F_i, Gen_2] closest to the 16.66ms grid) and keep all 3 ([F_i, Gen_1, Gen_2]) on the 3-frame step. This achieves your exact 24fps -> 72fps -> drop 12fps -> 60fps logic!
Case C (INTERPOLATE_2S — 12fps to 60fps):
Instruct RIFE 4.7 to generate 5x between frame_i and frame_j (timesteps = 0.2, 0.4, 0.6, 0.8), producing 5 frames (0ms, 16.6ms, 33.3ms, 50.0ms, 66.6ms). Output all 5 (or match needed_60fps_frames if a 23.976fps rounding tick occurs).
Case D (INTERPOLATE_3S — 8fps to 60fps):
Instruct RIFE 4.7 to generate 8x between frame_i and frame_j (producing 8 frames across 125ms).
Since 8fps -> 60fps requires 7.5 frames (needed_60fps_frames naturally alternates between 7 and 8), when needed_60fps_frames == 7, drop 1 generated frame (using uniform index selection np.linspace(0, 7, needed_60fps_frames, endpoint=False).round().astype(int)).
Case E (INTERPOLATE_4S — 6fps to 60fps):
Instruct RIFE 4.7 to generate 10x between frame_i and frame_j (needed_60fps_frames == 10). Output all 10 frames.
Batching Optimization for rife-ncnn-vulkan.exe on Windows:
If using the CLI rife-ncnn-vulkan.exe, batch all RIFE pairs in the current 30-frame window into ./temp_buffer/in/ and invoke rife-ncnn-vulkan.exe -m models/rife-v4.7 -g 0 (or use rife-ncnn-vulkan-python bindings if available so GPU initialization only happens once at program startup!).
IMPORTANT: Initializing Vulkan once per pair via CLI subprocess has high startup overhead on Windows. Therefore, in setup_rife.py / interpolator.py, either:
Prefer rife-ncnn-vulkan-python (persistent in-memory Vulkan session), OR
Run rife-ncnn-vulkan.exe once per 30-frame folder batch so the AMD iGPU stays warm and achieves the full 3–5 FPS!
'''