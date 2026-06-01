import { useState, useCallback, useRef, DragEvent } from "react";

/* ---------- types ---------- */

type Stage = "idle" | "uploading" | "processing" | "done" | "error";

interface VideoMeta {
  video_id: string;
  filename: string;
  size_mb: number;
  info: { duration: number; width: number; height: number; fps: number; codec: string };
}

interface Frame {
  filename: string;
  size_kb: number;
  url: string;
}

interface Result {
  video_id: string;
  info: VideoMeta["info"];
  frames: Frame[];
  subtitles: string;
  titles: string[];
}

/* ---------- api ---------- */

const API = ""; // nginx 代理，同源

async function uploadVideo(file: File): Promise<VideoMeta> {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${API}/api/upload`, { method: "POST", body: fd });
  if (!r.ok) throw new Error((await r.json()).detail ?? "上传失败");
  return r.json();
}

async function processVideo(videoId: string): Promise<Result> {
  const fd = new FormData();
  fd.append("video_id", videoId);
  const r = await fetch(`${API}/api/process`, { method: "POST", body: fd });
  if (!r.ok) throw new Error((await r.json()).detail ?? "处理失败");
  return r.json();
}

/* ---------- components ---------- */

export default function App() {
  const [stage, setStage] = useState<Stage>("idle");
  const [meta, setMeta] = useState<VideoMeta | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const run = useCallback(async (file: File) => {
    setStage("uploading");
    setError("");
    try {
      const m = await uploadVideo(file);
      setMeta(m);
      setStage("processing");
      const r = await processVideo(m.video_id);
      setResult(r);
      setStage("done");
    } catch (e: any) {
      setError(e.message);
      setStage("error");
    }
  }, []);

  const onDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files[0];
      if (f && f.type.startsWith("video/")) run(f);
    },
    [run]
  );

  const copyTitle = async (t: string) => {
    await navigator.clipboard.writeText(t);
  };

  return (
    <div className="app">
      {/* header */}
      <header className="hero">
        <h1>🎬 短视频 AI 工具箱</h1>
        <p>上传视频 · 自动提取封面帧 · AI 生成爆款标题</p>
      </header>

      {/* upload zone */}
      {(stage === "idle" || stage === "error") && (
        <section
          className={`dropzone ${dragOver ? "over" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
        >
          <div className="dropzone-inner">
            <span className="drop-icon">📁</span>
            <p className="drop-hint">拖拽视频到此处，或点击选择文件</p>
            <p className="drop-meta">支持 MP4 / MOV / AVI · 最大 500MB</p>
          </div>
          <input
            ref={inputRef}
            type="file"
            accept="video/*"
            style={{ display: "none" }}
            onChange={(e) => { const f = e.target.files?.[0]; if (f) run(f); }}
          />
        </section>
      )}
      {stage === "error" && <div className="error-msg">❌ {error}</div>}

      {/* uploading */}
      {stage === "uploading" && <StageBox emoji="📤" text="正在上传视频…" sub="" />}

      {/* processing */}
      {stage === "processing" && (
        <StageBox emoji="⚙️" text="AI 正在分析视频…" sub="关键帧提取 + 标题生成" meta={meta} />
      )}

      {/* results */}
      {stage === "done" && result && (
        <section className="results">
          {/* meta bar */}
          <div className="meta-bar">
            <span>⏱️ {result.info.duration?.toFixed(0)}s</span>
            <span>📐 {result.info.width}×{result.info.height}</span>
            <span>🎞️ {result.info.fps}fps</span>
            <span>📦 {meta?.size_mb}MB</span>
          </div>

          {/* frames */}
          <h2>🖼️ 关键帧（点击下载）</h2>
          <div className="frames-grid">
            {result.frames.map((f, i) => (
              <a key={f.filename} className="frame-card" href={f.url} download target="_blank" rel="noreferrer">
                <img src={f.url} alt={`Frame ${i + 1}`} />
                <span className="frame-badge">帧 {i + 1} · {f.size_kb}KB</span>
              </a>
            ))}
          </div>

          {/* titles */}
          <h2>📝 AI 推荐标题</h2>
          <ul className="titles-list">
            {result.titles.map((t, i) => (
              <li key={i}>
                <span className="title-num">{i + 1}</span>
                <span className="title-text">{t}</span>
                <button className="btn-copy" onClick={() => copyTitle(t)}>📋 复制</button>
              </li>
            ))}
          </ul>

          {/* reset */}
          <button className="btn-reset" onClick={() => { setStage("idle"); setResult(null); setMeta(null); }}>
            重新上传
          </button>
        </section>
      )}
    </div>
  );
}

function StageBox({ emoji, text, sub, meta }: { emoji: string; text: string; sub: string; meta?: VideoMeta | null }) {
  return (
    <section className="stage-box">
      <div className="spinner" />
      <p className="stage-text">{emoji} {text}</p>
      {sub && <p className="stage-sub">{sub}</p>}
      {meta && <p className="stage-meta">📁 {meta.filename} · {meta.size_mb}MB</p>}
    </section>
  );
}
