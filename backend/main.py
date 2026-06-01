"""
短视频 AI 工具箱 — 后端入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import router

app = FastAPI(title="Short Video AI Tools", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
async def root():
    return {"status": "ok", "service": "Short Video AI Tools"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
