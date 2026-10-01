# -*- coding: utf-8 -*-
"""
WavLM 추론 래퍼.

MOCK=1  → 모델 없이 그럴듯한 결과를 만든다. 스택 전체(업로드→큐→워커→DB→화면)를
          모델 없이도 끝까지 돌려볼 수 있어서, 발표 당일 안전장치로도 쓴다.
MOCK=0  → 학습 때 쓴 src/model.py 의 SERModel 을 그대로 불러와 best.pt 를 올린다.
          체크포인트 안에 학습 당시 cfg 가 통째로 들어 있어서(ck["cfg"]) 설정을 다시
          적을 필요가 없고, 감정 클래스 순서도 거기서 읽는다 ← 이게 제일 중요하다.
          (학습 코드의 클래스 순서: angry, sadness, happy, neutral, fear, disgust, surprise)
"""
import os, sys, math, hashlib, json
import numpy as np

# 폴백용 기본 순서 (MOCK 전용). 실제 추론은 체크포인트의 순서를 쓴다.
EMOTIONS = ["angry", "sadness", "neutral", "happy", "fear", "disgust", "surprise"]

_R = None          # 로드된 추론기


# ══════════════════════════════════════════════════════════════════
# 전처리 — 학습/평가 때(src/infer.py EmotionRecognizer._prep)와 똑같이 맞춘다.
#   평균 제거 + 피크 정규화(0.891). 이걸 빼먹으면 입력 분포가 달라져 정확도가 떨어진다.
# ══════════════════════════════════════════════════════════════════
def prep(y: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=np.float32)
    y = y - y.mean()
    m = float(np.abs(y).max())
    return (y / m * 0.891).astype(np.float32) if m > 1e-5 else y.astype(np.float32)


class _Recognizer:
    """학습 코드(model.py)를 그대로 가져다 쓰는 추론기."""

    def __init__(self, ckpt_path: str, ser_src: str, device: str = "cpu"):
        import torch
        self.torch = torch

        if not os.path.exists(ckpt_path):
            raise FileNotFoundError(
                f"체크포인트가 없어: {ckpt_path}\n"
                "  .env 의 CKPT_PATH 를 확인해줘. 학습 폴더를 마운트했다면 보통\n"
                "  /app/ser_src/work/ckpt/<런이름>/best.pt 형태야."
            )

        # 학습 코드 경로를 먼저 잡아야 model.py 를 import 할 수 있다
        for p in (os.path.join(ser_src, "src"), ser_src):
            if os.path.isdir(p) and p not in sys.path:
                sys.path.insert(0, p)
        try:
            from model import SERModel
        except Exception as e:                       # noqa: BLE001
            raise RuntimeError(
                f"학습 코드(model.py)를 못 찾았어 (SER_SRC={ser_src}). "
                f"docker-compose.yml 의 ../ser 마운트를 확인해줘. 원인: {e}"
            )

        # weights_only=False : 체크포인트에 cfg(dict)가 같이 들어 있어서 필요하다
        ck = torch.load(ckpt_path, map_location="cpu", weights_only=False)
        if "cfg" not in ck or "model" not in ck:
            raise RuntimeError("체크포인트에 cfg/model 키가 없어 — 학습 때 저장 형식이 다른 것 같아.")

        self.cfg = ck["cfg"]
        self.classes = list(self.cfg["label"]["classes"])     # ← 순서 그대로 사용
        self.sr = int(self.cfg["audio"]["sample_rate"])

        model = SERModel(self.cfg)

        # 레이어 가중합 크기가 다르면 조용히 틀린 모델이 된다 → 먼저 잡는다
        w_ck = ck["model"].get("layer_w")
        if w_ck is not None and tuple(w_ck.shape) != tuple(model.layer_w.shape):
            raise RuntimeError(
                f"layer_w 크기가 안 맞아 (체크포인트 {tuple(w_ck.shape)} vs 지금 {tuple(model.layer_w.shape)}). "
                "transformers 버전이 학습 때와 달라 hidden_states 개수가 바뀐 경우야. "
                "requirements.txt 의 transformers 버전을 학습 환경과 맞춰줘."
            )

        missing, unexpected = model.load_state_dict(ck["model"], strict=False)
        if missing:
            print(f"[infer] 주의: 못 채운 파라미터 {len(missing)}개 (예: {missing[:3]})")
        if unexpected:
            print(f"[infer] 주의: 남는 파라미터 {len(unexpected)}개 (예: {unexpected[:3]})")

        self.device = torch.device(device)
        self.model = model.to(self.device).eval()
        torch.set_num_threads(max(1, (os.cpu_count() or 4)))

        # 선택: 로짓 보정(τ). 체크포인트 폴더에 prior.json 이 있으면 자동 적용.
        self.tau, self.log_prior = 0.0, None
        pj = os.path.join(os.path.dirname(ckpt_path), "prior.json")
        if os.path.exists(pj):
            try:
                d = json.load(open(pj, encoding="utf-8"))
                self.tau = float(d.get("tau", 0.0))
                pri = np.array([float(d["prior"][c]) for c in self.classes], dtype=np.float64)
                self.log_prior = np.log(pri / pri.sum())
                print(f"[infer] 로짓 보정 적용 τ={self.tau}")
            except Exception as e:                   # noqa: BLE001
                print(f"[infer] prior.json 읽기 실패 — 보정 없이 진행: {e}")

        ep = self.cfg.get("_epoch") or ck.get("epoch")
        print(f"[infer] 모델 로드 완료 · {self.cfg['model']['backbone']} · "
              f"클래스 {self.classes} · epoch={ep} · device={device}")

    def predict(self, chunks, batch: int = 4):
        torch = self.torch
        out = []
        with torch.no_grad():
            for i in range(0, len(chunks), batch):
                part = chunks[i:i + batch]
                x = torch.from_numpy(np.stack([c[1] for c in part])).to(self.device)
                logits = self.model(x).float()
                if self.log_prior is not None and self.tau:
                    logits = logits - torch.tensor(
                        self.tau * self.log_prior, dtype=logits.dtype, device=logits.device)
                p = torch.softmax(logits, dim=-1).cpu().numpy()
                for (t, _), row in zip(part, p):
                    out.append({"t": float(t),
                                "probs": {c: float(v) for c, v in zip(self.classes, row)}})
        return out


# ══════════════════════════════════════════════════════════════════
def load(ckpt_path: str, ser_src: str, device: str = "cpu", mock: bool = True):
    global _R
    if mock:
        _R = "mock"
        return _R
    if _R is None or _R == "mock":
        _R = _Recognizer(ckpt_path, ser_src, device)
    return _R


def classes():
    return _R.classes if isinstance(_R, _Recognizer) else EMOTIONS


def predict(chunks, device: str = "cpu", mock: bool = True, seed_key: str = ""):
    """[(t, wave), ...] → [{'t':초, 'probs':{감정:확률}}, ...]"""
    if mock or not isinstance(_R, _Recognizer):
        return _mock_predict(chunks, seed_key)
    return _R.predict(chunks)


# ══════════════════════════════════════════════════════════════════
# MOCK: 파일 이름으로 시드를 고정해 같은 파일이면 같은 결과가 나오게
# ══════════════════════════════════════════════════════════════════
def _mock_predict(chunks, seed_key: str = ""):
    seed = int(hashlib.md5((seed_key or "demo").encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    n = len(chunks)
    out = []
    for i, (t, wave) in enumerate(chunks):
        u = i / max(1, n - 1)
        energy = float(np.sqrt(np.mean(np.asarray(wave, dtype=np.float64) ** 2)) + 1e-6)
        heat = math.exp(-((u - 0.45) ** 2) / 0.05)          # 중반에 고조
        calm = math.exp(-((u - 0.9) ** 2) / 0.02)
        base = {
            "neutral":  0.45 * (1 - heat) + 0.15,
            "angry":    0.55 * heat + 0.05 + min(0.25, energy * 2),
            "sadness":  0.30 * math.exp(-((u - 0.68) ** 2) / 0.03) + 0.05,
            "happy":    0.35 * calm + 0.03,
            "fear":     0.08 * heat + 0.02,
            "disgust":  0.10 * heat + 0.02,
            "surprise": 0.06 + 0.04 * rng.random(),
        }
        noise = {k: max(1e-3, v * (0.85 + 0.3 * rng.random())) for k, v in base.items()}
        sharp = {k: v ** 3.4 for k, v in noise.items()}
        if rng.random() < 0.05:
            sharp = {k: v ** 0.35 for k, v in sharp.items()}
        z = sum(sharp.values())
        out.append({"t": t, "probs": {k: v / z for k, v in sharp.items()}})
    return out
