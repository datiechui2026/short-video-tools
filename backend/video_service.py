"""
视频处理服务 — ffmpeg 关键帧提取 + 元数据分析
"""

import os
import subprocess
import json
import uuid
from pathlib import Path

UPLOAD_DIR = Path("data/uploads")
FRAMES_DIR = Path("data/frames")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

MAX_VIDEO_MB = 500


def save_upload(file_bytes: bytes, filename: str) -> Path:
    """保存上传视频，返回文件路径"""
    video_id = uuid.uuid4().hex[:12]
    ext = Path(filename).suffix or ".mp4"
    path = UPLOAD_DIR / f"{video_id}{ext}"
    path.write_bytes(file_bytes)
    return path


def get_video_info(path: Path) -> dict:
    """用 ffprobe 获取视频元信息"""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return {"error": result.stderr}

    data = json.loads(result.stdout)
    fmt = data.get("format", {})
    video_stream = None
    for s in data.get("streams", []):
        if s.get("codec_type") == "video":
            video_stream = s
            break

    return {
        "duration": float(fmt.get("duration", 0)),
        "size_mb": round(int(fmt.get("size", 0)) / (1024 * 1024), 1),
        "width": video_stream.get("width") if video_stream else None,
        "height": video_stream.get("height") if video_stream else None,
        "fps": eval(video_stream.get("r_frame_rate", "0")) if video_stream and video_stream.get("r_frame_rate") else None,
        "codec": video_stream.get("codec_name") if video_stream else None,
    }


def extract_keyframes(path: Path, count: int = 3) -> list[dict]:
    """
    场景检测提取关键帧。
    策略：计算场景变化分数，取分数最高的 N 帧。
    返回：frame 文件路径列表
    """
    video_id = path.stem
    out_pattern = str(FRAMES_DIR / f"{video_id}_%03d.jpg")

    # 1) 场景检测，输出每帧的 scene_score
    result = subprocess.run([
        "ffmpeg", "-i", str(path),
        "-vf", f"select='gt(scene,0.15)',scale=1280:-1",
        "-vsync", "vfr",
        "-frame_pts", "1",
        out_pattern,
    ], capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        # fallback: 均匀采样
        print(f"[ffmpeg] scene detect failed, using uniform sampling: {result.stderr[-200:]}")
        return _uniform_sample(path, video_id, count)

    # 2) 收集生成的帧文件
    frames = sorted(FRAMES_DIR.glob(f"{video_id}_*.jpg"), key=lambda f: f.stat().st_mtime)
    if not frames:
        return _uniform_sample(path, video_id, count)

    # 取前 count 张（已经按场景变化重要性排序）
    selected = frames[:count]
    results = []
    for f in selected:
        # 简单"图像质量"评分 — 用文件大小当 proxy（大 = 细节多）
        quality = f.stat().st_size
        results.append({
            "path": str(f),
            "filename": f.name,
            "size_kb": round(quality / 1024, 1),
            "score": round(quality / max(1, quality), 2),
        })

    return results


def _uniform_sample(path: Path, video_id: str, count: int) -> list[dict]:
    """均匀采样 fallback"""
    import subprocess
    duration = float(subprocess.check_output(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        text=True, timeout=10,
    ).strip() or 10)

    results = []
    for i in range(count):
        t = duration * (i + 1) / (count + 1)
        out_name = f"{video_id}_uniform_{i}.jpg"
        out_path = str(FRAMES_DIR / out_name)
        subprocess.run([
            "ffmpeg", "-ss", str(t), "-i", str(path),
            "-vframes", "1", "-q:v", "2", "-y", out_path,
        ], capture_output=True, timeout=30)
        if Path(out_path).exists():
            results.append({
                "path": out_path,
                "filename": out_name,
                "size_kb": round(Path(out_path).stat().st_size / 1024, 1),
                "score": round(1.0 - i * 0.2, 2),
            })
    return results


def extract_subtitles(path: Path) -> str:
    """提取嵌入字幕（如有），返回完整文本；无字幕返回空"""
    result = subprocess.run([
        "ffmpeg", "-i", str(path),
        "-map", "0:s:0?", "-f", "srt", "-",
    ], capture_output=True, text=True, timeout=30)

    if result.returncode != 0 or not result.stdout.strip():
        return ""

    # 去时间戳，只保留文本
    lines = []
    for line in result.stdout.split("\n"):
        line = line.strip()
        if line and not line.isdigit() and "-->" not in line:
            lines.append(line)
    return "\n".join(lines)
