"""
AI 服务 — DeepSeek API 调用
"""

import os
import httpx

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

TITLE_PROMPT = """你是一个短视频标题专家。根据以下视频信息，生成 5 个爆款标题。

视频时长：{duration}秒
视频分辨率：{resolution}
字幕/文案内容（如有）：
{subtitle}

要求：
1. 标题 10-25 字
2. 至少 2 个包含数字（如 "3个方法..."）
3. 至少 1 个使用疑问句
4. 至少 1 个使用"你"开头
5. 适合抖音/小红书风格

直接返回 JSON 数组：
["标题1", "标题2", "标题3", "标题4", "标题5"]"""


async def generate_titles(duration: float, resolution: str, subtitle: str = "") -> list[str]:
    """生成 5 个短视频标题"""
    if not DEEPSEEK_API_KEY:
        return _fallback_titles(duration)

    prompt = TITLE_PROMPT.format(
        duration=int(duration),
        resolution=resolution or "未知",
        subtitle=subtitle[:2000] or "无字幕内容",
    )

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{DEEPSEEK_BASE}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 500,
            },
        )

    if resp.status_code != 200:
        print(f"[AI] DeepSeek error: {resp.status_code} {resp.text[:200]}")
        return _fallback_titles(duration)

    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()

    # 解析 JSON 数组（可能被 markdown 包裹）
    import re
    match = re.search(r'\[.*?\]', content, re.DOTALL)
    if match:
        try:
            import json
            titles = json.loads(match.group())
            if isinstance(titles, list) and len(titles) >= 3:
                return titles[:5]
        except:
            pass

    # fallback: 按行解析
    lines = [l.strip().lstrip("1234567890. -") for l in content.split("\n") if l.strip()]
    return lines[:5] if len(lines) >= 3 else _fallback_titles(duration)


def _fallback_titles(duration: float) -> list[str]:
    mins = int(duration / 60)
    return [
        f"这{mins}分钟的视频，改变了我对XX的认知",
        f"做了{mins}分钟后，我后悔没有早点知道",
        f"3个{mins}分钟的短视频技巧，第2个真的绝了",
        f"你以为的XX，其实是这样（{mins}分钟真相）",
        f"我花了{mins}分钟，总结了3个核心干货",
    ]
