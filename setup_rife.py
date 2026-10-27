'''
(Sub-Agent 1: Zero-Friction RIFE 4.7 Installer)
Check if RIFE_EXE_PATH and MODELS_DIR / "rife-v4.7" exist.
If not, use urllib.request to query or download the official Windows binary release zip from https://github.com/nihui/rife-ncnn-vulkan/releases (and if the zip only has up to rife-v4.6, automatically fetch the rife-v4.7 .param and .bin weights from the official repo/mirror into models/rife-v4.7/).
Also verify ffmpeg is accessible on Windows PATH (or imageio_ffmpeg.get_ffmpeg_exe() as automatic fallback so the user never gets a FileNotFoundError on Windows).
'''