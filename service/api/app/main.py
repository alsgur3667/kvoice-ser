# -*- coding: utf-8 -*-
"""
보이스 코리안 API

  POST /analyses          오디오 업로드 → Storage 저장 → DB에 queued 등록 (워커가 처리)
  GET  /analyses/{id}     상태 + 요약 + 3초 구간 전체
  GET  /analyses          목록 (대시보드용)
  GET  /stats             일별 집계
  POST /feedback          오분류 신고 (재학습 데이터로 쌓임)
  GET  /health            헬스체크
  GET  /system            시스템 상태 (컨테이너·모델·큐)
"""
import uuid, datetime, os
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response

from .config import settings
from . import db, rules
from .schemas import AnalysisCreated, Analysis, FeedbackIn

app = FastAPI(title="보이스 코리안 API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ALLOWED = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm", ".mp4"}


@app.on_event("startup")
def _dev_worker():
    """
    Supabase 설정이 비어 있으면(메모리 모드) 워커를 같은 프로세스에서 돌린다.
    → docker 없이 `uvicorn app.main:app` 하나만 띄워도 전체 흐름을 확인할 수 있다.
    운영(도커+Supabase)에서는 worker 컨테이너가 따로 돈다.
    """
    if db.MEMORY:
        import threading
        from .worker import main as worker_main
        threading.Thread(target=worker_main, daemon=True).start()
        print("[api] 메모리 모드 — 워커를 같은 프로세스에서 실행")


@app.get("/health")
def health():
    return {
        "ok": True,
        "mock": bool(settings.mock),
        "store": "supabase" if not db.MEMORY else "memory(dev)",
        "store_ok": db.ping(),
        "model_version": "mock" if settings.mock else settings.model_version,
        "max_upload_mb": settings.max_upload_mb,
        "max_duration_sec": settings.max_duration_sec,
        "domains": {k: v["name"] for k, v in rules.DOMAINS.items()},
        "regions": {k: v["name"] for k, v in rules.REGIONS.items()},
    }


SYS_STARTED = datetime.datetime.now(datetime.timezone.utc)
HB_PATH = os.environ.get("WORKER_HB", "/models/worker_hb.json")


@app.get("/system")
def system():
    """시연용 시스템 상태 — 컨테이너·모델·큐가 실제로 살아 있는지 한 번에."""
    import json as _json, time as _time

    # ① API (이 응답이 온 것 자체가 증거)
    api = {
        "ok": True,
        "uptime_sec": round((datetime.datetime.now(datetime.timezone.utc) - SYS_STARTED).total_seconds()),
        "port": int(os.environ.get("PORT", 8000)),
    }

    # ② 저장소 (Supabase REST 왕복 시간)
    t0 = _time.time()
    store_ok = db.ping()
    store = {
        "ok": bool(store_ok),
        "kind": "supabase" if not db.MEMORY else "memory(dev)",
        "latency_ms": round((_time.time() - t0) * 1000),
    }

    # ③ 워커 (공유 볼륨의 심박 파일)
    worker = {"ok": False, "state": "unknown", "age_sec": None}
    try:
        hb = _json.load(open(HB_PATH, encoding="utf-8"))
        age = _time.time() - float(hb.get("ts") or 0)
        worker = {
            "ok": age < 15,                       # 폴링 2초 → 15초면 확실히 죽은 것
            "state": hb.get("state", "unknown"),
            "age_sec": round(age, 1),
            "uptime_sec": hb.get("uptime_sec"),
            "processed": hb.get("processed", 0),
            "failed": hb.get("failed", 0),
            "last_job": hb.get("last_job"),
            "model_loaded": bool(hb.get("model_loaded")),
            "model_error": hb.get("model_error"),
            "classes": hb.get("classes"),
            "device": hb.get("device"),
            "poll_sec": hb.get("poll_sec"),
        }
    except FileNotFoundError:
        worker["state"] = "no-heartbeat"
    except Exception as e:                        # noqa: BLE001
        worker["state"] = f"error: {str(e)[:60]}"

    # ④ 모델
    ckpt_ok = os.path.exists(settings.ckpt_path)
    model = {
        "ok": bool(worker.get("model_loaded")) or bool(settings.mock),
        "version": "mock" if settings.mock else settings.model_version,
        "mock": bool(settings.mock),
        "device": settings.device,
        "ckpt_path": settings.ckpt_path,
        "ckpt_exists": ckpt_ok,
        "ckpt_mb": round(os.path.getsize(settings.ckpt_path) / 1048576) if ckpt_ok else None,
        "loaded": bool(worker.get("model_loaded")),
        "classes": worker.get("classes"),
        "win_sec": settings.win_sec,
        "hop_sec": settings.hop_sec,
        "sample_rate": settings.sample_rate,
    }

    # ⑤ 큐
    try:
        rows = db.select("analyses", "select=id,status&order=created_at.desc&limit=200")
    except Exception:
        rows = []
    queue = {
        "queued": sum(1 for r in rows if r.get("status") == "queued"),
        "running": sum(1 for r in rows if r.get("status") == "running"),
        "failed": sum(1 for r in rows if r.get("status") == "failed"),
        "done": sum(1 for r in rows if r.get("status") == "done"),
    }

    parts = [api["ok"], store["ok"], worker["ok"], model["ok"]]
    return {
        "ok": all(parts),
        "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "api": api, "store": store, "worker": worker, "model": model, "queue": queue,
        "containers": {"api": api["ok"], "worker": worker["ok"], "web": True},
        "limits": {"max_upload_mb": settings.max_upload_mb, "max_duration_sec": settings.max_duration_sec},
    }


@app.post("/analyses", response_model=AnalysisCreated)
async def create_analysis(
    file: UploadFile = File(...),
    domain: str = Form("counsel"),
    region: str = Form("seoul"),
):
    if domain not in rules.DOMAINS:
        raise HTTPException(400, f"모르는 현장: {domain}")
    if region not in rules.REGIONS:
        raise HTTPException(400, f"모르는 지역: {region}")
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED:
        raise HTTPException(400, f"지원하지 않는 형식: {ext or '알 수 없음'}")

    raw = await file.read()
    limit = settings.max_upload_mb * 1024 * 1024
    if len(raw) > limit:
        raise HTTPException(
            413, f"파일이 너무 커 ({len(raw)/1048576:.1f}MB) — {settings.max_upload_mb}MB 이하만 올릴 수 있어. "
                 f"긴 녹음이면 필요한 구간만 잘라서 올려줘.")

    key = f"{datetime.date.today().isoformat()}/{uuid.uuid4().hex}{ext}"
    db.upload_audio(key, raw, file.content_type or "application/octet-stream")

    row = db.insert("analyses", {
        "filename": file.filename,
        "storage_path": key,
        "domain": domain,
        "region": region,
        "threshold": rules.threshold(domain, region if region != "auto" else "seoul"),
        "status": "queued",
    })
    return AnalysisCreated(id=row["id"], status=row["status"])


@app.get("/analyses/{analysis_id}", response_model=Analysis)
def get_analysis(analysis_id: str):
    rows = db.select("analyses", f"select=*&id=eq.{analysis_id}")
    if not rows:
        raise HTTPException(404, "없는 분석이야")
    a = rows[0]
    segs = []
    if a["status"] == "done":
        segs = db.select("segments", f"select=*&analysis_id=eq.{analysis_id}&order=idx.asc")
    a["segments"] = segs
    return a


MIME = {".wav": "audio/wav", ".mp3": "audio/mpeg", ".m4a": "audio/mp4", ".mp4": "audio/mp4",
        ".flac": "audio/flac", ".ogg": "audio/ogg", ".webm": "audio/webm"}


@app.get("/analyses/{analysis_id}/audio")
def get_audio(analysis_id: str):
    """결과 화면에서 실제로 소리를 들을 수 있게 원본 음성을 내려준다."""
    rows = db.select("analyses", f"select=storage_path,filename&id=eq.{analysis_id}")
    if not rows or not rows[0].get("storage_path"):
        raise HTTPException(404, "음성 파일이 없어")
    path = rows[0]["storage_path"]
    ext = os.path.splitext(path)[1].lower()
    mime = MIME.get(ext, "application/octet-stream")

    if not db.MEMORY:
        # 1순위: Supabase 서명 링크로 넘긴다 (구간 탐색(Range)도 Supabase가 처리)
        try:
            return RedirectResponse(db.sign_audio(path), status_code=307)
        except Exception as e:                      # noqa: BLE001
            print(f"[api] 서명 링크 실패 → 서버가 직접 중계함: {e}")

    # 2순위(안전망): 서버가 파일을 받아서 그대로 내려준다
    try:
        data = db.download_audio(path)
    except Exception as e:                          # noqa: BLE001
        raise HTTPException(502, f"음성을 가져오지 못했어: {e}")
    return Response(data, media_type=mime,
                    headers={"Accept-Ranges": "bytes", "Cache-Control": "private, max-age=600",
                             "Content-Length": str(len(data))})


@app.get("/analyses")
def list_analyses(domain: Optional[str] = None, limit: int = 20):
    q = f"select=id,created_at,filename,domain,region_used,status,duration_sec,flow,risk_seconds,hold_ratio,top_emotion&order=created_at.desc&limit={limit}"
    if domain:
        q += f"&domain=eq.{domain}"
    return db.select("analyses", q)


@app.get("/stats")
def stats(domain: Optional[str] = None, days: int = 7):
    """대시보드용 집계. 뷰 대신 서버에서 계산한다 — 쿼리가 하나고, 바꾸기도 쉽다."""
    import collections, datetime as dt

    rows = db.select("analyses",
                     "select=id,created_at,filename,domain,region,region_used,status,duration_sec,"
                     "flow,risk_seconds,hold_ratio,top_emotion,n_windows,summary"
                     "&order=created_at.desc&limit=500")
    if domain:
        rows = [r for r in rows if r.get("domain") == domain]
    done = [r for r in rows if r.get("status") == "done"]
    n = len(done) or 1

    # ── 일별 대표 감정 분포 ─────────────────────────────────────
    by_day = collections.OrderedDict()
    for r in reversed(done):                       # 오래된 것부터
        day = (r.get("created_at") or "")[:10]
        if not day:
            continue
        d = by_day.setdefault(day, {"day": day, "calls": 0, "emotions": collections.Counter()})
        d["calls"] += 1
        if r.get("top_emotion"):
            d["emotions"][r["top_emotion"]] += 1
    daily = [{"day": v["day"][5:].replace("-", "/"), "calls": v["calls"], "emotions": dict(v["emotions"])}
             for v in list(by_day.values())[-days:]]

    # ── 지역 보정 분포 ─────────────────────────────────────────
    reg = collections.Counter((r.get("region_used") or r.get("region") or "seoul") for r in done)
    regions = [{"key": k, "count": c, "pct": round(100 * c / n)} for k, c in reg.most_common()]

    # ── 확인이 필요한 건 (위험 구간 긴 순 → 보류 많은 순) ───────
    def risk_key(r):
        return (-(r.get("risk_seconds") or 0), -float(r.get("hold_ratio") or 0))
    recent = []
    for r in sorted(done, key=risk_key)[:6]:
        sm = r.get("summary") or {}
        recent.append({
            "id": r["id"],
            "label": (r.get("filename") or r["id"][:8]),
            "dur": r.get("duration_sec"),
            "region": r.get("region_used") or r.get("region"),
            "signal": sm.get("signal") or "-",
            "evidence": sm.get("evidence") or "-",
            "risk": r.get("risk_seconds") or 0,
            "hold": float(r.get("hold_ratio") or 0),
            "flow": r.get("flow") or "-",
        })

    fb = db.select("feedback", "select=id,said,correct,created_at&order=created_at.desc&limit=500")
    risky = [r for r in done if (r.get("risk_seconds") or 0) > 30]

    return {
        "kpi": {
            "calls": len(done),
            "minutes": round(sum(float(r.get("duration_sec") or 0) for r in done) / 60, 1),
            "risky": len(risky),
            "risky_pct": round(100 * len(risky) / n, 1),
            "avg_risk_sec": round(sum((r.get("risk_seconds") or 0) for r in done) / n, 1),
            "avg_hold": round(sum(float(r.get("hold_ratio") or 0) for r in done) / n, 4),
            "segments": sum(int(r.get("n_windows") or 0) for r in done),
        },
        "daily": daily,
        "regions": regions,
        "recent": recent,
        "model": {
            "version": "mock" if settings.mock else settings.model_version,
            "mock": bool(settings.mock),
            "device": settings.device,
            "threshold": rules.DOMAINS.get(domain or "counsel", {}).get("thr"),
            "feedback": len(fb),
            "retrain_at": 30,
        },
        "queued": sum(1 for r in rows if r.get("status") in ("queued", "running")),
        "failed": sum(1 for r in rows if r.get("status") == "failed"),
    }


@app.post("/feedback")
def add_feedback(f: FeedbackIn):
    db.insert("feedback", f.model_dump())
    return {"ok": True}
