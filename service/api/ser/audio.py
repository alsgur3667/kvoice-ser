# -*- coding: utf-8 -*-
"""오디오 전처리: 어떤 포맷이든 16kHz 모노로 → 3초 창(1.5초 겹침)으로 자르기."""
import subprocess, tempfile, os
import numpy as np
import soundfile as sf


def to_wav16k(raw: bytes, sample_rate: int = 16000) -> np.ndarray:
    """ffmpeg로 16kHz 모노 변환 후 float32 배열로."""
    with tempfile.TemporaryDirectory() as d:
        src, dst = os.path.join(d, "in"), os.path.join(d, "out.wav")
        with open(src, "wb") as f:
            f.write(raw)
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
               "-i", src, "-ac", "1", "-ar", str(sample_rate), "-f", "wav", dst]
        subprocess.run(cmd, check=True)
        x, sr = sf.read(dst, dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    return x


def windows(x: np.ndarray, sr: int = 16000, win_sec: float = 3.0, hop_sec: float = 1.5):
    """[(시작초, 파형조각), ...] — 학습 때와 같은 3초/1.5초 규칙."""
    w, h = int(win_sec * sr), int(hop_sec * sr)
    out = []
    if len(x) < w:                       # 3초보다 짧으면 0으로 채워 한 조각
        pad = np.zeros(w, dtype="float32")
        pad[:len(x)] = x
        return [(0.0, pad)]
    for i in range(0, len(x) - w + 1, h):
        out.append((i / sr, x[i:i + w]))
    return out
