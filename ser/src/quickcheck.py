# -*- coding: utf-8 -*-
"""
사전 점검 — 긴 전처리/학습을 시작하기 전에 2분 안에 막힐 곳을 전부 찾는다.
  python src/quickcheck.py --config configs/base.yaml
"""
import argparse, os, sys, shutil, random, time

def ok(m):   print(f"  [OK]   {m}")
def bad(m):  print(f"  [FAIL] {m}")
def warn(m): print(f"  [WARN] {m}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/base.yaml")
    args = ap.parse_args()
    fails = 0

    print("\n=== 1. 파이썬 / 패키지 ===")
    print(f"  python {sys.version.split()[0]}  ({sys.executable})")
    mods = {}
    for m in ["torch", "transformers", "librosa", "soundfile", "pandas",
              "numpy", "sklearn", "yaml", "tqdm"]:
        try:
            mod = __import__(m)
            mods[m] = getattr(mod, "__version__", "?")
            ok(f"{m} {mods[m]}")
        except Exception as e:
            bad(f"{m} 없음 ({e})"); fails += 1
    if "torch" not in mods:
        print("\n먼저 setup.bat 을 실행하세요."); sys.exit(1)

    print("\n=== 2. GPU ===")
    import torch
    if not torch.cuda.is_available():
        bad("CUDA 사용 불가 — CPU 로는 학습이 사실상 불가능합니다.")
        warn("torch 를 CUDA 빌드로 다시 설치하세요:")
        warn("  pip install torch --index-url https://download.pytorch.org/whl/cu121")
        fails += 1
    else:
        for i in range(torch.cuda.device_count()):
            p = torch.cuda.get_device_properties(i)
            ok(f"cuda:{i}  {p.name}  {p.total_memory/1024**3:.1f}GB  sm_{p.major}{p.minor}")
        ok(f"torch {torch.__version__} / cuda {torch.version.cuda}")
        if torch.cuda.is_bf16_supported():
            ok("bf16 지원 — config 의 precision: bf16 그대로 사용")
        else:
            warn("bf16 미지원 — fp16 로 바꾸고 GradScaler 를 써야 합니다")

    print("\n=== 3. 설정 / 경로 ===")
    import yaml, pandas as pd
    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    raw = cfg["paths"]["raw_root"]; work = cfg["paths"]["work_root"]
    if os.path.isdir(raw): ok(f"데이터 루트: {raw}")
    else: bad(f"데이터 루트 없음: {raw}  <- configs 의 raw_root 를 고치세요"); fails += 1

    total_rows = 0
    for src, name in cfg["paths"]["csv"].items():
        p = os.path.join(raw, name)
        if not os.path.exists(p):
            bad(f"CSV 없음: {p}"); fails += 1; continue
        df = None
        for enc in ("cp949", "utf-8-sig", "utf-8"):
            try:
                df = pd.read_csv(p, encoding=enc); used = enc; break
            except (UnicodeDecodeError, UnicodeError):
                continue
        if df is None:
            bad(f"{name}: 인코딩 판별 실패"); fails += 1; continue
        total_rows += len(df)
        ok(f"{name}: {len(df):,}행 ({used})")
        d = os.path.join(raw, cfg["paths"]["wav_subdir"][src])
        if os.path.isdir(d): ok(f"  wav 폴더: {cfg['paths']['wav_subdir'][src]}")
        else: bad(f"  wav 폴더 없음: {d}"); fails += 1

    print("\n=== 4. 오디오 샘플 읽기 (20개) ===")
    import soundfile as sf, librosa, numpy as np
    random.seed(0); miss = 0; rates = {}; durs = []; samples = []
    for src, name in cfg["paths"]["csv"].items():
        p = os.path.join(raw, name)
        if not os.path.exists(p): continue
        for enc in ("cp949", "utf-8-sig", "utf-8"):
            try: df = pd.read_csv(p, encoding=enc); break
            except (UnicodeDecodeError, UnicodeError): continue
        ids = df.iloc[:, 0].astype(str).tolist()
        for wid in random.sample(ids, min(7, len(ids))):
            fp = os.path.join(raw, cfg["paths"]["wav_subdir"][src], wid + ".wav")
            if not os.path.exists(fp): miss += 1; continue
            try:
                info = sf.info(fp)
                rates[info.samplerate] = rates.get(info.samplerate, 0) + 1
                durs.append(info.frames / info.samplerate)
                samples.append(fp)
            except Exception as e:
                bad(f"읽기 실패 {os.path.basename(fp)}: {e}"); fails += 1
    if miss: bad(f"wav 누락 {miss}/20 — zip 압축을 다 풀었는지 확인"); fails += 1
    else: ok("샘플 20개 전부 읽힘")
    if durs:
        ok(f"샘플레이트 {rates}  |  길이 평균 {np.mean(durs):.2f}s "
           f"(min {min(durs):.2f} / max {max(durs):.2f})")
    if samples:
        librosa.load(samples[0], sr=16000, mono=True)          # 워밍업(첫 호출은 import 비용 포함)
        t0 = time.time()
        for fp2 in samples[:5]:
            librosa.load(fp2, sr=16000, mono=True)
        el = (time.time() - t0) / len(samples[:5])
        ok(f"16kHz 리샘플 1개 평균 {el*1000:.0f}ms  "
           f"-> 44,000개 약 {max(1, round(44000*el/8/60))}분 (8 workers 기준)")

    print("\n=== 5. 디스크 ===")
    os.makedirs(work, exist_ok=True)
    free = shutil.disk_usage(work).free / 1024**3
    need = 6.0
    (ok if free > need else bad)(f"작업 폴더 여유 {free:.1f}GB (필요 약 {need:.0f}GB)")
    if free <= need: fails += 1

    print("\n=== 6. 백본 다운로드 ===")
    try:
        from transformers import AutoConfig
        AutoConfig.from_pretrained(cfg["model"]["backbone"])
        ok(f"{cfg['model']['backbone']} 접근 가능")
    except Exception as e:
        bad(f"백본을 받을 수 없음: {str(e)[:120]}"); fails += 1
        warn("사내망/방화벽이면 HF_ENDPOINT 미러를 쓰거나 미리 받아두세요.")

    print("\n" + "=" * 52)
    if fails == 0:
        print("  전부 통과. run_all.bat 을 실행하세요.")
    else:
        print(f"  {fails}건 실패 — 위 [FAIL] 을 먼저 해결하세요.")
    print("=" * 52 + "\n")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
