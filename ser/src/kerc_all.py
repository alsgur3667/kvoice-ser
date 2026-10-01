# -*- coding: utf-8 -*-
"""
KERC(한국 영화 감정 영상) 한 방 처리
  다운로드 -> 라벨 컬럼 자동 탐지 -> mp4에서 16kHz wav 추출 -> 평가까지

  python src/kerc_all.py --ckpt work/ckpt/pilot_1006/best.pt
"""
import argparse, os, sys, glob, subprocess, shutil, collections
import pandas as pd

ALIAS = {
    "neu": "neutral", "neutral": "neutral", "중립": "neutral",
    "ang": "angry", "anger": "angry", "angry": "angry", "분노": "angry", "화남": "angry",
    "sad": "sadness", "sadness": "sadness", "슬픔": "sadness",
    "hap": "happy", "happy": "happy", "happiness": "happy", "joy": "happy", "기쁨": "happy",
    "fea": "fear", "fear": "fear", "fearful": "fear", "두려움": "fear", "공포": "fear",
    "dis": "disgust", "disgust": "disgust", "disgusted": "disgust", "혐오": "disgust",
    "sur": "surprise", "surprise": "surprise", "surprised": "surprise", "놀람": "surprise",
}


def step(n, msg): print(f"\n{'='*60}\n [{n}] {msg}\n{'='*60}", flush=True)


def ffmpeg_bin():
    p = shutil.which("ffmpeg")
    if p: return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("ffmpeg 이 없습니다.  uv pip install imageio-ffmpeg  후 다시 실행하세요.")


def download(comp):
    try:
        import kagglehub
    except ImportError:
        sys.exit("kagglehub 이 없습니다.  uv pip install kagglehub  후 다시 실행하세요.")
    tok = os.path.join(os.path.expanduser("~"), ".kaggle", "kaggle.json")
    if not os.path.exists(tok) and not os.environ.get("KAGGLE_KEY"):
        print(f"[!] {tok} 이 없습니다.")
        print("    kaggle.com -> 프로필 -> Settings -> API -> Create New Token")
        print("    받은 kaggle.json 을 위 경로에 두세요.\n")
    try:
        return kagglehub.competition_download(comp)
    except Exception as e:
        msg = str(e)
        if "403" in msg or "Forbidden" in msg:
            sys.exit(f"접근 거부. kaggle.com/c/{comp} 에서 Rules 를 먼저 동의하세요.\n  {msg[:160]}")
        sys.exit(f"다운로드 실패: {msg[:200]}")


def read_any(p, **kw):
    for enc in ("utf-8-sig", "cp949", "utf-8"):
        try: return pd.read_csv(p, encoding=enc, **kw)
        except (UnicodeDecodeError, UnicodeError): continue
    return None


def auto_detect(root):
    """mp4 파일명과 CSV 값을 대조해 라벨 CSV / ID 컬럼 / 감정 컬럼을 스스로 찾는다."""
    mp4 = {}
    for p in glob.glob(os.path.join(root, "**", "*.mp4"), recursive=True):
        mp4[os.path.splitext(os.path.basename(p))[0]] = p
    if not mp4: sys.exit(f"{root} 안에 mp4 가 없습니다.")
    print(f"mp4 {len(mp4):,}개 발견")

    best = None
    for c in sorted(glob.glob(os.path.join(root, "**", "*.csv"), recursive=True)):
        df = read_any(c)
        if df is None or df.empty: continue
        lab_cols, id_cols = [], []
        for col in df.columns:
            v = df[col].astype(str).str.strip()
            frac_lab = v.str.lower().isin(ALIAS).mean()
            if frac_lab >= 0.8: lab_cols.append((col, frac_lab))
            stems = v.map(lambda x: os.path.splitext(x)[0])
            frac_id = stems.isin(mp4).mean()
            if frac_id >= 0.5: id_cols.append((col, frac_id, int(stems.isin(mp4).sum())))
        if lab_cols and id_cols:
            lab = max(lab_cols, key=lambda t: t[1])
            idc = max(id_cols, key=lambda t: t[2])
            print(f"  {os.path.relpath(c, root):40s} 라벨='{lab[0]}' ID='{idc[0]}' 매칭 {idc[2]:,}개")
            if best is None or idc[2] > best[3]:
                best = (c, idc[0], lab[0], idc[2])
    if best is None:
        print("\n자동 탐지 실패. CSV 컬럼을 직접 확인해야 합니다:")
        for c in sorted(glob.glob(os.path.join(root, "**", "*.csv"), recursive=True))[:10]:
            df = read_any(c, nrows=3)
            if df is not None:
                print(f"\n--- {os.path.relpath(c, root)} ---")
                print("  컬럼:", list(df.columns))
                print(df.head(2).to_string(index=False, max_colwidth=24))
        sys.exit("\n위 컬럼명을 알려주면 수동으로 지정해 드립니다.")
    print(f"\n선택: {os.path.relpath(best[0], root)}  (ID '{best[1]}' / 감정 '{best[2]}')")
    return best[0], best[1], best[2], mp4


def extract(csv_path, id_col, lab_col, mp4, out_dir, sr, limit):
    ff = ffmpeg_bin()
    os.makedirs(out_dir, exist_ok=True)
    meta = read_any(csv_path)
    items = list(meta.itertuples())
    if limit: items = items[:limit]

    rows, miss, bad, unmapped = [], 0, 0, collections.Counter()
    for i, r in enumerate(items):
        key = os.path.splitext(str(getattr(r, id_col)).strip())[0]
        src = mp4.get(key)
        if src is None: miss += 1; continue
        lab = ALIAS.get(str(getattr(r, lab_col)).strip().lower())
        if lab is None: unmapped[str(getattr(r, lab_col))] += 1; continue
        dst = os.path.join(out_dir, f"{key}_{lab[:3]}.wav")
        if not os.path.exists(dst):
            cmd = [ff, "-v", "error", "-y", "-i", src, "-vn",
                   "-ac", "1", "-ar", str(sr), "-acodec", "pcm_s16le", dst]
            ok = subprocess.run(cmd, capture_output=True).returncode == 0
            if not ok or not os.path.exists(dst) or os.path.getsize(dst) < 2000:
                bad += 1
                if os.path.exists(dst): os.remove(dst)
                continue
        rows.append({"emotion": lab, "path": os.path.basename(dst), "clip": key})
        if (i + 1) % 100 == 0:
            print(f"  {i+1:,}/{len(items):,}   추출 {len(rows):,}", flush=True)

    if not rows: sys.exit("추출된 클립이 없습니다.")
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "segments.csv"), index=False, encoding="utf-8-sig")
    print(f"\n{len(df):,}개 추출 -> {out_dir}")
    if miss: print(f"  mp4 없음 {miss:,}")
    if bad: print(f"  오디오 없음/실패 {bad:,}")
    if unmapped: print(f"  매핑 안 된 라벨: {dict(unmapped.most_common(8))}")
    print("\n라벨 분포:\n" + df.emotion.value_counts().to_string())
    return out_dir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comp", default="2020kerc")
    ap.add_argument("--root", default=None, help="이미 받아놨으면 그 경로")
    ap.add_argument("--out", default=None)
    ap.add_argument("--ckpt", default="work/ckpt/pilot_1006/best.pt")
    ap.add_argument("--sr", type=int, default=16000)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-eval", action="store_true")
    args = ap.parse_args()

    out = args.out or os.path.join(os.path.expanduser("~"), "Desktop", "kerc_audio")

    step(1, "데이터 확보")
    if args.root and os.path.isdir(args.root):
        root = args.root; print(f"기존 경로 사용: {root}")
    else:
        root = download(args.comp); print(f"받은 경로: {root}")

    step(2, "라벨 자동 탐지")
    csv_path, id_col, lab_col, mp4 = auto_detect(root)

    step(3, "mp4 -> 16kHz wav 추출")
    if os.path.exists(os.path.join(out, "segments.csv")):
        print(f"이미 추출돼 있음: {out}  (다시 하려면 폴더를 지우세요)")
    else:
        extract(csv_path, id_col, lab_col, mp4, out, args.sr, args.limit)

    if args.no_eval: 
        print(f"\n평가하려면:\n  python src/eval_external.py --ckpt {args.ckpt} --dir \"{out}\" --csv segments.csv")
        return

    step(4, "교차 검증")
    if not os.path.exists(args.ckpt):
        print(f"체크포인트가 없습니다: {args.ckpt}"); return
    here = os.path.dirname(os.path.abspath(__file__))
    subprocess.run([sys.executable, os.path.join(here, "eval_external.py"),
                    "--ckpt", args.ckpt, "--dir", out, "--csv", "segments.csv",
                    "--th", "0.70", "--out", os.path.join(out, "kerc_eval.png")])


if __name__ == "__main__":
    main()
