# 短视频 AI 工具箱

上传视频 → AI 一键生成封面图 + 爆款标题 + 口播文案

## 技术栈

- **后端**: Python FastAPI + ffmpeg + DeepSeek API + 阿里云视觉智能
- **前端**: React + Vite + TypeScript + Tailwind CSS
- **部署**: nginx + systemd (Tencent Cloud CVM)

## 功能

| 功能 | 说明 |
|------|------|
| 关键帧提取 | ffmpeg 场景检测，自动挑 3 张最佳封面候选 |
| AI 封面生成 | 抠图 + 背景替换 + 文字叠加 |
| AI 标题生成 | DeepSeek 根据视频内容生成 5 个标题 |
| 字幕提取 | 提取嵌入字幕或 whisper 语音转文字 |

## MVP 范围

上传视频 → 3 张封面图 + 5 个标题 → 一键下载

## 开发

```bash
# 后端
cd backend && pip install -r requirements.txt && uvicorn main:app --reload

# 前端
cd frontend && npm install && npm run dev
```
