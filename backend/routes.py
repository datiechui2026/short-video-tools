"""
API 路由
"""

import os
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from video_service import save_upload, get_video_info, extract_keyframes, extract_subtitles
from ai_service import generate_titles

router = APIRouter(prefix="/api")
MAX_MB = 500


@router.get("/health")
async def api_health():
    return {"status": "healthy"}


@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """上传视频，返回 video_id + 元信息"""
    if not file.filename:
        raise HTTPException(400, "文件名不能为空")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_MB:
        raise HTTPException(400, f"文件不能超过 {MAX_MB}MB，当前 {size_mb:.1f}MB")

    path = save_upload(content, file.filename)
    info = get_video_info(path)

    return {
        "video_id": path.stem,
        "filename": file.filename,
        "size_mb": round(size_mb, 1),
        "info": info,
    }


@router.post("/process")
async def process_video(video_id: str = Form(...)):
    """
    处理视频：关键帧提取 + 字幕提取 + AI 标题生成。
    这是异步的，前端可以分步调用。
    """
    # 找到视频文件
    matches = list(Path("data/uploads").glob(f"{video_id}.*"))
    if not matches:
        raise HTTPException(404, f"视频不存在: {video_id}")
    video_path = matches[0]

    # 1) 视频基本信息
    info = get_video_info(video_path)

    # 2) 关键帧提取
    frames = extract_keyframes(video_path, count=3)

    # 3) 字幕提取
    subtitle = extract_subtitles(video_path)

    # 4) AI 标题生成
    resolution = f"{info.get('width', '?')}x{info.get('height', '?')}"
    titles = await generate_titles(info.get("duration", 60), resolution, subtitle)

    return {
        "video_id": video_id,
        "info": info,
        "frames": [
            {
                "filename": f["filename"],
                "size_kb": f["size_kb"],
                "url": f"/api/frames/{f['filename']}",
            }
            for f in frames
        ],
        "subtitles": subtitle[:500] if subtitle else "",
        "titles": titles,
    }


@router.get("/frames/{filename}")
async def get_frame(filename: str):
    """返回关键帧图片"""
    path = Path("data/frames") / filename
    if not path.exists():
        raise HTTPException(404, "图片不存在")
    return FileResponse(str(path), media_type="image/jpeg")


@router.get("/video/{video_id}")
async def get_video_meta(video_id: str):
    """单独查询视频元信息"""
    matches = list(Path("data/uploads").glob(f"{video_id}.*"))
    if not matches:
        raise HTTPException(404)
    info = get_video_info(matches[0])
    return {"video_id": video_id, "info": info, "filename": matches[0].name}
