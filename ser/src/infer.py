# -*- coding: utf-8 -*-
"""8단계: 추론 — 파일/스트림 공용. 긴 상담 통화는 청크 슬라이딩으로 감정 타임라인 생성."""
import os, sys, numpy as np, torch, librosa
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import SERModel


class EmotionRecognizer:
    def __init__(self, ckpt, device=None):
        ck = torch.load(ckpt, map_location="cpu", weights_only=False)
        self.cfg = ck["cfg"]; self.classes = self.cfg["label"]["classes"]
        self.sr = self.cfg["audio"]["sample_rate"]
        self.dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model = SERModel(self.cfg); self.model.load_state_dict(ck["model"])
        self.model.to(self.dev).eval()

    def _prep(self, y):
        y = y - y.mean()
        m = np.abs(y).max()
        return (y / m * 0.891 if m > 1e-5 else y).astype(np.float32)

    @torch.no_grad()
    def predict(self, wav_path_or_array, sr=None):
        y = (librosa.load(wav_path_or_array, sr=self.sr, mono=True)[0]
             if isinstance(wav_path_or_array, str)
             else librosa.resample(np.asarray(wav_path_or_array, np.float32),
                                   orig_sr=sr, target_sr=self.sr))
        y = self._prep(y)
        x = torch.from_numpy(y)[None].to(self.dev)
        with torch.autocast("cuda", dtype=torch.bfloat16, enabled=self.dev.type == "cuda"):
            pr = torch.softmax(self.model(x).float(), -1)[0].cpu().numpy()
        i = int(pr.argmax())
        return {"label": self.classes[i], "confidence": float(pr[i]),
                "probs": {c: float(v) for c, v in zip(self.classes, pr)}}

    @torch.no_grad()
    def timeline(self, wav_path, win=3.0, hop=1.5):
        """상담 통화 전체를 3초 창/1.5초 홉으로 훑어 감정 변화 곡선을 뽑는다."""
        y = self._prep(librosa.load(wav_path, sr=self.sr, mono=True)[0])
        W, H = int(win * self.sr), int(hop * self.sr)
        out = []
        for s in range(0, max(1, len(y) - W + 1), H):
            seg = y[s:s + W]
            if len(seg) < self.sr * 0.8: break
            x = torch.from_numpy(seg)[None].to(self.dev)
            with torch.autocast("cuda", dtype=torch.bfloat16, enabled=self.dev.type == "cuda"):
                pr = torch.softmax(self.model(x).float(), -1)[0].cpu().numpy()
            out.append({"t": round(s / self.sr, 2),
                        "label": self.classes[int(pr.argmax())],
                        "confidence": float(pr.max()),
                        "probs": {c: round(float(v), 4) for c, v in zip(self.classes, pr)}})
        return out


if __name__ == "__main__":
    import json
    r = EmotionRecognizer(sys.argv[1])
    print(json.dumps(r.predict(sys.argv[2]), ensure_ascii=False, indent=2))
