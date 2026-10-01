# -*- coding: utf-8 -*-
"""
현장(domain) 해석 규칙 + 지역(region) 말투 보정.
데모 화면에 하드코딩돼 있던 규칙을 서버로 옮긴 것 — 화면과 서버가 같은 규칙을 쓴다.
"""
from typing import Dict, List

from .config import settings

EMOTIONS = ["angry", "sadness", "neutral", "happy", "fear", "disgust", "surprise"]
EMO_KO = {"angry": "분노", "sadness": "슬픔", "neutral": "중립", "happy": "기쁨",
          "fear": "공포", "disgust": "혐오", "surprise": "놀람"}

# ── 지역별 보정: 그 지역 말투 때문에 과하게 나오는 감정을 눌러준다 ──────────
REGIONS: Dict[str, dict] = {
    "seoul":   {"name": "수도권 · 표준어", "adj": {},                                        "thr": 0.0},
    "gyeong":  {"name": "경상", "adj": {"angry": 0.78, "surprise": 1.05, "neutral": 1.14},   "thr": 0.0},
    "jeolla":  {"name": "전라", "adj": {"sadness": 0.85, "neutral": 1.10},                   "thr": 0.0},
    "chung":   {"name": "충청", "adj": {"sadness": 0.90, "neutral": 1.06},                   "thr": 0.0},
    "gangwon": {"name": "강원", "adj": {"surprise": 0.87, "neutral": 1.05},                  "thr": 0.0},
    "jeju":    {"name": "제주", "adj": {},                                                   "thr": 0.05},
    "auto":    {"name": "자동 감지", "adj": {},                                              "thr": 0.0},
}

# ── 현장별 규칙 ──────────────────────────────────────────────────────────
DOMAINS: Dict[str, dict] = {
    "counsel": {"name": "상담센터", "rule": "상담 v1", "thr": 0.70, "watch": "angry",
                "min_run": 30, "signal": "에스컬레이션 후보",
                "action": "수퍼바이저 연결 · 통화 후 상담사 휴식"},
    "edu":     {"name": "교육 현장", "rule": "교육 v1", "thr": 0.70, "watch": "fear",
                "min_run": 20, "signal": "발표 불안 구간",
                "action": "도입부 반복 연습 · 첫 30초 대본 고정"},
    "care":    {"name": "돌봄 · 안부 확인", "rule": "돌봄 v1", "thr": 0.72, "watch": "sadness",
                "min_run": 90, "signal": "우울 신호 (지속형)",
                "action": "이번 주 방문 우선순위 · 복지사 확인"},
    "hr":      {"name": "채용 면접", "rule": "면접 v0", "thr": 0.70, "watch": "fear",
                "min_run": 20, "signal": "초반 긴장 (참고용)",
                "action": "긴장 완화 질문 먼저 배치 · 평가에는 사용하지 않음"},
}


def threshold(domain: str, region: str) -> float:
    base = settings.hold_threshold or DOMAINS[domain]["thr"]
    return round(base + REGIONS[region]["thr"], 4)


def calibrate(probs: Dict[str, float], region: str) -> Dict[str, float]:
    """지역 보정 후 다시 정규화."""
    adj = REGIONS.get(region, REGIONS["seoul"])["adj"]
    if not adj:
        return dict(probs)
    out = {k: v * adj.get(k, 1.0) for k, v in probs.items()}
    z = sum(out.values()) or 1.0
    return {k: v / z for k, v in out.items()}


def valence_arousal(probs: Dict[str, float]) -> (float, float):
    """7감정 확률 → 긍부정/각성도 (그래프용 근사값)."""
    V = {"happy": 0.8, "surprise": 0.2, "neutral": 0.0, "fear": -0.5,
         "sadness": -0.6, "disgust": -0.7, "angry": -0.8}
    A = {"angry": 0.9, "fear": 0.8, "surprise": 0.75, "happy": 0.55,
         "disgust": 0.6, "neutral": 0.3, "sadness": 0.25}
    return (sum(probs[k] * V[k] for k in probs), sum(probs[k] * A[k] for k in probs))


def summarize(segments: List[dict], domain: str, region_used: str, hop: float) -> dict:
    """구간 리스트 → 요약(감정 흐름 / 전환 횟수 / 위험 구간 / 보류 비율 / 해석)."""
    d = DOMAINS[domain]
    solid = [s for s in segments if not s["hold"]]
    hold_ratio = 1 - len(solid) / max(1, len(segments))

    # 연속 같은 감정 묶기
    runs, cur = [], None
    for s in segments:
        e = s["emotion"] if not s["hold"] else "hold"
        if cur and cur["emotion"] == e:
            cur["end"] = s["t_start"] + hop
        else:
            cur = {"emotion": e, "start": s["t_start"], "end": s["t_start"] + hop}
            runs.append(cur)
    big = [r for r in runs if r["emotion"] != "hold" and (r["end"] - r["start"]) >= 10]

    flow, prev = [], None
    for r in big:
        if r["emotion"] != prev:
            flow.append(EMO_KO[r["emotion"]])
            prev = r["emotion"]
    flow_txt = " → ".join(flow[:3] + [flow[-1]]) if len(flow) > 4 else " → ".join(flow)
    if not flow_txt:                       # 너무 짧은 녹음 등
        from collections import Counter
        c = Counter(s["emotion"] for s in solid)
        flow_txt = EMO_KO[c.most_common(1)[0][0]] + " 중심" if c else "판단 보류 위주"

    # 위험 구간: 현장이 지켜보는 감정이 min_run초 이상 이어진 가장 긴 구간
    watch = d["watch"]
    watch_runs = [r for r in big if r["emotion"] == watch and (r["end"] - r["start"]) >= d["min_run"]]
    risk = max(watch_runs, key=lambda r: r["end"] - r["start"], default=None)
    risk_sec = int(risk["end"] - risk["start"]) if risk else 0

    top = max(solid, key=lambda s: s["probs"][s["emotion"]], default=None)
    top_pct = int(round(top["probs"][top["emotion"]] * 100)) if top else 0

    return {
        "flow": flow_txt,
        "transitions": max(0, len(big) - 1),
        "hold_ratio": round(hold_ratio, 4),
        "risk_seconds": risk_sec,
        "risk_start": int(risk["start"]) if risk else None,
        "top_emotion": top["emotion"] if top else None,
        "summary": {
            "signal": d["signal"] if risk else "특이 신호 없음",
            "evidence": f"{EMO_KO[watch]} {top_pct}% · {risk_sec}초 연속" if risk else "지속 구간 없음",
            "rule": f'{d["rule"]} · {EMO_KO[watch]} {d["thr"]:.2f} 이상 {d["min_run"]}초 지속',
            "action": d["action"] if risk else "추가 조치 불필요",
            "region": REGIONS[region_used]["name"],
            "threshold": threshold(domain, region_used),
        },
    }
