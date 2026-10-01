# -*- coding: utf-8 -*-
"""오디오 한 건 → 3초 구간 결과 + 요약. (API도 워커도 이걸 쓴다)"""
import time
from typing import Dict, List, Tuple

from .config import settings
from . import rules
from ser import audio as A
from ser import infer as I


def detect_region(chunks, filename: str = "") -> str:
    """
    '자동 감지' 자리. 지금은 표준어로 처리한다.
    나중에 방언 판별기(멜 특징 기반 6-클래스)를 붙이면 여기만 바꾸면 된다.
    """
    return "seoul"


def analyze(raw: bytes, filename: str, domain: str, region: str) -> Tuple[List[dict], dict, dict]:
    t0 = time.time()
    x = A.to_wav16k(raw, settings.sample_rate)
    x = I.prep(x)                      # 학습 때와 같은 정규화 (평균 제거 + 피크 0.891)
    duration = len(x) / settings.sample_rate
    if duration > settings.max_duration_sec:
        raise ValueError(f"너무 긴 파일이야 ({duration:.0f}초). 최대 {settings.max_duration_sec}초.")

    chunks = A.windows(x, settings.sample_rate, settings.win_sec, settings.hop_sec)

    I.load(settings.ckpt_path, settings.ser_src, settings.device, mock=bool(settings.mock))
    t_inf = time.time()
    preds = I.predict(chunks, settings.device, mock=bool(settings.mock), seed_key=filename)
    inf_sec = round(time.time() - t_inf, 2)

    region_used = detect_region(chunks, filename) if region == "auto" else region
    thr = rules.threshold(domain, region_used)

    segments: List[dict] = []
    for i, p in enumerate(preds):
        raw_probs = p["probs"]
        cal = rules.calibrate(raw_probs, region_used)
        top = max(cal, key=cal.get)
        conf = cal[top]
        v, a = rules.valence_arousal(cal)
        segments.append({
            "idx": i,
            "t_start": round(p["t"], 3),
            "emotion": top,
            "confidence": round(conf, 4),
            "hold": bool(conf < thr),          # 확신이 낮으면 판단 보류
            "valence": round(v, 4),
            "arousal": round(a, 4),
            "probs": {k: round(v2, 4) for k, v2 in cal.items()},
            "probs_raw": {k: round(v2, 4) for k, v2 in raw_probs.items()},
        })

    summary = rules.summarize(segments, domain, region_used, settings.hop_sec)
    meta = {
        "duration_sec": round(duration, 2),
        "n_windows": len(segments),
        "region_used": region_used,
        "threshold": thr,
        "model_version": ("mock" if settings.mock else settings.model_version),
        "elapsed_sec": round(time.time() - t0, 2),
        "infer_sec": inf_sec,
    }
    return segments, summary, meta
