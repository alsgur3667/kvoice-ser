# -*- coding: utf-8 -*-
"""
2단계: 실제 wav -> 학습용 16kHz 캐시 (여기서 '음성을 데이터화' 한다)

원본: 48kHz / mono / 16bit / 평균 3.7초 -> 총 약 45시간, 15.5GB
캐시: 16kHz mono -> 약 5GB. 매 epoch 리샘플링하는 낭비를 없애 학습속도 2~3배.

하는 일:
  1) 48k -> 16k 리샘플 (사전학습 모델 입력 규격)
  2) DC offset 제거 + 피크 정규화  <- 녹음 레벨 차이를 '감정 단서'로 오학습하는 것 방지
  3) 앞뒤 무음 트림 (top_db)
  4) 길이 통계 산출 -> max_sec 결정 근거

사용:
  python src/preprocess_audio.py --config configs/base.yaml --workers 8
"""
import argparse, os, sys, json
import numpy as np, pandas as pd, yaml, soundfile as sf
from concurrent.futures import ProcessPoolExecutor
from functools import partial
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wpath import wp

try:
    import librosa
except ImportError:
    sys.exit("pip install librosa soundfile")


def process_one(row, sr, peak_norm, trim_db, min_sec, max_sec, out_dir, fmt):
    wid, path = row
    dst = os.path.join(out_dir, f"{wid}.{fmt}")
    if os.path.exists(dst):
        try:
            info = sf.info(dst); return (wid, info.frames / info.samplerate, "cached")
        except Exception:
            pass
    try:
        y, _ = librosa.load(path, sr=sr, mono=True)
    except Exception as e:
        return (wid, 0.0, f"read_error:{e}")

    y = y - np.mean(y)                                   # DC offset
    if trim_db:
        y, _ = librosa.effects.trim(y, top_db=trim_db)
    if len(y) < min_sec * sr:
        return (wid, len(y) / sr, "too_short")
    # 여기서는 max_sec 로 자르지 않는다.
    # 캐시는 '원본에 가까운' 상태로 두고, 길이 제한은 학습 시 dataset.py 가 적용한다.
    # (pilot 은 6초, full 은 8초처럼 설정을 바꿔도 캐시를 다시 만들 필요가 없다)
    HARD_CAP = 30.0
    if len(y) > HARD_CAP * sr:
        c = len(y) // 2; h = int(HARD_CAP * sr) // 2
        y = y[c - h: c + h]
    if peak_norm:
        m = np.abs(y).max()
        if m < 1e-5:
            return (wid, len(y) / sr, "silent")
        y = y / m * 0.891                                # -1 dBFS

    if fmt == "wav":
        sf.write(dst, y.astype(np.float32), sr, subtype="PCM_16")
    else:
        np.save(dst, y.astype(np.float32))
    return (wid, len(y) / sr, "ok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/base.yaml")
    ap.add_argument("--workers", type=int, default=os.cpu_count() // 2)
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    a = cfg["audio"]; work = cfg["paths"]["work_root"]

    mani = pd.read_csv(wp(cfg, "manifest.csv"))
    out_dir = os.path.join(work, f"audio_{a['sample_rate']}")
    os.makedirs(out_dir, exist_ok=True)

    fn = partial(process_one, sr=a["sample_rate"], peak_norm=a["peak_norm"],
                 trim_db=a["trim_db"], min_sec=a["min_sec"], max_sec=a["max_sec"],
                 out_dir=out_dir, fmt=a["cache_format"])
    rows = list(zip(mani.wav_id.astype(str), mani.wav_path))

    res = []
    with ProcessPoolExecutor(args.workers) as ex:
        for i, r in enumerate(ex.map(fn, rows, chunksize=64)):
            res.append(r)
            if (i + 1) % 2000 == 0:
                print(f"  {i+1:,}/{len(rows):,}", flush=True)

    rdf = pd.DataFrame(res, columns=["wav_id", "dur", "status"])
    print("\n[status]\n", rdf.status.str.split(":").str[0].value_counts())

    ok = rdf[rdf.status.isin(["ok", "cached"])]
    print(f"\n[duration] n={len(ok):,}  mean={ok.dur.mean():.2f}s  "
          f"median={ok.dur.median():.2f}s  total={ok.dur.sum()/3600:.1f}h")
    for q in (0.5, 0.8, 0.9, 0.95, 0.99):
        print(f"  p{int(q*100)} = {ok.dur.quantile(q):.2f}s")
    over = (ok.dur > a["max_sec"]).mean()
    print(f"  max_sec({a['max_sec']}s) 초과 비율 {over*100:.1f}% "
          f"-> 학습 때 랜덤 crop 됩니다 (캐시는 그대로 보존)")

    # wav_id -> (dur, status) 매핑. merge 대신 map 을 쓴다(중복 id 가 있어도 행이 늘지 않음)
    rdf = rdf.drop_duplicates("wav_id", keep="last").set_index("wav_id")
    key = mani.wav_id.astype(str)
    mani["cache_path"] = key.map(lambda i: os.path.join(out_dir, f"{i}.{a['cache_format']}"))
    mani["dur"] = key.map(rdf["dur"])
    mani["status"] = key.map(rdf["status"])
    n_before = len(mani)
    mani = mani[mani.status.isin(["ok", "cached"])].copy()
    if len(mani) != n_before:
        print(f"[filter] 전처리 실패/너무 짧음 {n_before - len(mani):,}개 제외")
    mani.to_csv(wp(cfg, "manifest_proc.csv"), index=False, encoding="utf-8-sig")
    print(f"\n[saved] {wp(cfg, 'manifest_proc.csv')} ({len(mani):,}행)")


if __name__ == "__main__":
    main()
