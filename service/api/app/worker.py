# -*- coding: utf-8 -*-
"""
워커: DB에서 queued 를 하나씩 집어 실제 추론을 돌린다.
API와 분리해 두면 (1) 업로드 응답이 바로 떨어지고 (2) 무거운 추론이 웹을 막지 않는다.
docker compose up --scale worker=2 로 늘릴 수도 있다.
"""
import json, os, time, traceback

from .config import settings
from . import db
from .pipeline import analyze

# ── 워커 생존 신호 ────────────────────────────────────────────
# api 컨테이너와 ./models 볼륨을 공유하므로, 여기에 심박을 적으면
# api 가 /system 에서 읽어 "워커가 살아 있는가"를 판단할 수 있다.
HB_PATH = os.environ.get("WORKER_HB", "/models/worker_hb.json")
_STATE = {"processed": 0, "failed": 0, "last_job": None, "model_loaded": False,
          "started_at": time.time()}


def beat(state: str, **extra) -> None:
    d = {
        "ts": time.time(),
        "state": state,                       # loading | idle | busy
        "pid": os.getpid(),
        "uptime_sec": round(time.time() - _STATE["started_at"]),
        "device": settings.device,
        "mock": bool(settings.mock),
        "model_version": settings.model_version,
        "poll_sec": settings.worker_poll_sec,
        **_STATE, **extra,
    }
    d.pop("started_at", None)
    try:
        tmp = HB_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
        os.replace(tmp, HB_PATH)
    except Exception:                          # 심박 실패가 작업을 막으면 안 된다
        pass


def warm_model() -> None:
    """기동하자마자 체크포인트를 메모리에 올린다.
    (1) 대시보드에 '모델 로드 완료'를 정직하게 띄울 수 있고
    (2) 첫 분석이 느려지는 일이 없어진다."""
    beat("loading")
    try:
        from ser import infer as I
        I.load(settings.ckpt_path, settings.ser_src, settings.device, mock=bool(settings.mock))
        _STATE["model_loaded"] = True
        try:
            _STATE["classes"] = list(I.classes())
        except Exception:
            pass
        print("[worker] 모델 예열 완료")
    except Exception as e:                     # noqa: BLE001
        _STATE["model_error"] = str(e)[:200]
        print(f"[worker] 모델 예열 실패 — 첫 요청 때 다시 시도: {e}")


def handle(row: dict) -> None:
    aid = row["id"]
    print(f"[worker] start {aid} · {row['domain']} · {row['region']}")
    raw = db.download_audio(row["storage_path"])
    segments, summary, meta = analyze(raw, row.get("filename") or aid, row["domain"], row["region"])

    db.insert_many("segments", [dict(s, analysis_id=aid) for s in segments])
    db.update("analyses", {"id": aid}, {
        "status": "done",
        "finished_at": "now()",
        "duration_sec": meta["duration_sec"],
        "n_windows": meta["n_windows"],
        "region_used": meta["region_used"],
        "threshold": meta["threshold"],
        "model_version": meta["model_version"],
        "hold_ratio": summary["hold_ratio"],
        "flow": summary["flow"],
        "transitions": summary["transitions"],
        "risk_seconds": summary["risk_seconds"],
        "top_emotion": summary["top_emotion"],
        "summary": summary["summary"],
    })
    _STATE["processed"] += 1
    _STATE["last_job"] = {
        "id": aid, "at": time.time(),
        "windows": meta["n_windows"], "elapsed_sec": meta["elapsed_sec"],
        "infer_sec": meta.get("infer_sec"), "domain": row["domain"], "region": meta["region_used"],
    }
    print(f"[worker] done  {aid} · {meta['n_windows']}구간 · 전체 {meta['elapsed_sec']}초 (추론 {meta.get('infer_sec')}초) · {meta['model_version']}")


def main() -> None:
    print(f"[worker] 대기 중 (MOCK={settings.mock}, device={settings.device})")
    warm_model()
    while True:
        row = None
        try:
            beat("idle")
            row = db.claim_next_queued()
            if not row:
                time.sleep(settings.worker_poll_sec)
                continue
            beat("busy", job_id=row["id"])
            handle(row)
            beat("idle")
        except KeyboardInterrupt:
            break
        except Exception as e:                       # noqa: BLE001
            traceback.print_exc()
            _STATE["failed"] += 1
            _STATE["last_error"] = str(e)[:200]
            beat("idle")
            try:
                if row:
                    db.update("analyses", {"id": row["id"]},
                              {"status": "failed", "error": str(e)[:500], "finished_at": "now()"})
            except Exception:
                pass
            time.sleep(settings.worker_poll_sec)


if __name__ == "__main__":
    main()
