"""
共享夹具：生成测试视频 → 上传 → 返回 video_id
"""

import subprocess
import tempfile
from pathlib import Path

import httpx
import pytest

BASE = "http://127.0.0.1:8001"


@pytest.fixture(scope="session")
def client():
    return httpx.Client(base_url=BASE, timeout=30)


@pytest.fixture(scope="session")
def test_video_path():
    """生成 3 秒测试视频 MP4"""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        path = f.name
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "testsrc=duration=3:size=640x480:rate=30",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            path,
        ],
        capture_output=True,
        check=True,
    )
    yield Path(path)
    Path(path).unlink(missing_ok=True)


@pytest.fixture(scope="session")
def video_id(client, test_video_path):
    """上传测试视频，返回 video_id"""
    with open(test_video_path, "rb") as f:
        r = client.post("/api/upload", files={"file": ("test.mp4", f, "video/mp4")})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "video_id" in data
    assert data["info"]["duration"] > 0
    return data["video_id"]


@pytest.fixture(scope="session")
def process_result(client, video_id):
    """处理视频，返回完整结果"""
    r = client.post("/api/process", data={"video_id": video_id})
    assert r.status_code == 200, r.text
    return r.json()
