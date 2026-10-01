# -*- coding: utf-8 -*-
"""
스모크 테스트: 업로드 → 큐 → 워커 → 결과까지 한 번에 확인.
사용법:  python scripts/smoke.py [API주소] [음성파일]
        python scripts/smoke.py http://localhost:8000 sample.wav
파일을 안 주면 12초짜리 테스트용 소리를 직접 만들어서 올린다.
"""
import io, sys, time, json, urllib.request
import numpy as np
import soundfile as sf
import httpx

API = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
PATH = sys.argv[2] if len(sys.argv) > 2 else None


def fake_wav(sec=12, sr=16000) -> bytes:
    t = np.linspace(0, sec, sec * sr, dtype="float32")
    rng = np.random.default_rng(0)
    x = (0.06 + 0.25 * np.exp(-((t - sec / 2) ** 2) / (sec / 3))) * np.sin(2 * np.pi * 190 * t)
    x *= rng.normal(1, 0.3, t.size)
    buf = io.BytesIO(); sf.write(buf, x.astype("float32"), sr, format="WAV")
    return buf.getvalue()


def main():
    h = httpx.get(f"{API}/health", timeout=10).json()
    print("health:", json.dumps(h, ensure_ascii=False))

    data = open(PATH, "rb").read() if PATH else fake_wav()
    name = PATH or "smoke.wav"
    r = httpx.post(f"{API}/analyses", timeout=120,
                   files={"file": (name, data, "audio/wav")},
                   data={"domain": "counsel", "region": "gyeong"})
    r.raise_for_status()
    aid = r.json()["id"]
    print("업로드 완료 · id =", aid)

    t0 = time.time()
    while time.time() - t0 < 600:
        a = httpx.get(f"{API}/analyses/{aid}", timeout=30).json()
        print(f"  status={a['status']} ({time.time()-t0:.0f}s)")
        if a["status"] == "done":
            print("구간:", a["n_windows"], "| 흐름:", a["flow"],
                  "| 위험:", a["risk_seconds"], "초 | 보류:", round(float(a["hold_ratio"]) * 100, 1), "%")
            print("해석:", json.dumps(a["summary"], ensure_ascii=False))
            print("첫 구간:", json.dumps(a["segments"][0], ensure_ascii=False)[:200])
            return
        if a["status"] == "failed":
            print("실패:", a["error"]); return
        time.sleep(2)
    print("시간 초과")


if __name__ == "__main__":
    main()
