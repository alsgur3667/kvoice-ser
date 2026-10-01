# -*- coding: utf-8 -*-
"""
KERC / KVDERW (한국 영화 감정 영상) -> 오디오 교차검증셋으로 변환

1단계(기본): 내려받은 폴더 구조와 CSV 컬럼을 훑어 보여준다.
2단계(--extract): mp4 에서 16kHz mono wav 를 뽑고 segments.csv 를 만든다.
             그러면 eval_external.py 가 그대로 읽을 수 있다.

  python src/kerc_prep.py --root <kagglehub 경로>
  python src/kerc_prep.py --root <경로> --extract --label-csv train.csv --id-col clip --label-col emotion
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


def ffmpeg_bin():
    """시스템 ffmpeg 가 없으면 imageio-ffmpeg 의 번들 바이너리를 쓴다."""
    p = shutil.which("ffmpeg")
    if p: return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit("ffmpeg 이 없습니다.  pip install imageio-ffmpeg  후 다시 실행하세요.")


def inspect(root):
    print(f"\n[root] {root}\n")
    ext = collections.Counter()
    sample = {}
    for dp, _, fns in os.walk(root):
        for fn in fns:
            e = os.path.splitext(fn)[1].lower()
            ext[e] += 1
            sample.setdefault(e, os.path.join(dp, fn))
    print("=== 파일 종류 ===")
    for e, n in ext.most_common():
        print(f"  {e or '(확장자없음)':10s} {n:>6,}   예: {os.path.basename(sample[e])}")

    print("\n=== 상위 폴더 ===")
    for d in sorted(os.listdir(root))[:20]:
        q = os.path.join(root, d)
        if os.path.isdir(q):
            print(f"  {d}/  ({sum(len(f) for _,_,f in os.walk(q)):,} files)")

    csvs = sorted(glob.glob(os.path.join(root, "**", "*.csv"), recursive=True))
    print(f"\n=== CSV {len(csvs)}개 ===")
    for c in csvs:
        try:
            for enc in ("utf-8-sig", "cp949", "utf-8"):
                try: d = pd.read_csv(c, encoding=enc, nrows=5); break
                except (UnicodeDecodeError, UnicodeError): continue
            full = None
            for enc in ("utf-8-sig", "cp949", "utf-8"):
                try: full = pd.read_csv(c, encoding=enc); break
                except (UnicodeDecodeError, UnicodeError): continue
            print(f"\n--- {os.path.relpath(c, root)}  ({len(full):,}행) ---")
            print("  컬럼:", list(d.columns))
            print(d.head(3).to_string(index=False, max_colwidth=28))
            # 감정처럼 보이는 컬럼 후보
            for col in full.columns:
                vals = full[col].astype(str).str.lower().str.strip().unique()
                hit = sum(1 for v in vals[:40] if v in ALIAS)
                if hit >= 3:
                    print(f"  ** 감정 컬럼 후보: '{col}'  값={list(vals)[:10]}")
        except Exception as e:
            print(f"  (읽기 실패 {os.path.basename(c)}: {str(e)[:70]})")
    print("\n위 내용을 보고 --extract 단계의 --label-csv / --id-col / --label-col 을 정하세요.")


def extract(root, out_dir, label_csv, id_col, label_col, sr, limit):
    ff = ffmpeg_bin()
    print(f"[ffmpeg] {ff}")
    os.makedirs(out_dir, exist_ok=True)

    lp = label_csv if os.path.isabs(label_csv) else os.path.join(root, label_csv)
    if not os.path.exists(lp):
        hits = glob.glob(os.path.join(root, "**", os.path.basename(label_csv)), recursive=True)
        if not hits: sys.exit(f"라벨 CSV 를 못 찾았습니다: {label_csv}")
        lp = hits[0]
    for enc in ("utf-8-sig", "cp949", "utf-8"):
        try: meta = pd.read_csv(lp, encoding=enc); break
        except (UnicodeDecodeError, UnicodeError): continue
    print(f"[labels] {lp}  {len(meta):,}행")
    if id_col not in meta.columns or label_col not in meta.columns:
        sys.exit(f"컬럼이 없습니다. 있는 컬럼: {list(meta.columns)}")

    # mp4 인덱스 (파일명 -> 경로)
    mp4 = {}
    for p in glob.glob(os.path.join(root, "**", "*.mp4"), recursive=True):
        mp4[os.path.splitext(os.path.basename(p))[0]] = p
    print(f"[video] mp4 {len(mp4):,}개")

    rows, miss, bad, unmapped = [], 0, 0, collections.Counter()
    items = list(meta.itertuples())
    if limit: items = items[:limit]
    for i, r in enumerate(items):
        key = str(getattr(r, id_col)).strip()
        key = os.path.splitext(key)[0]
        src = mp4.get(key)
        if src is None:
            miss += 1; continue
        lab = ALIAS.get(str(getattr(r, label_col)).strip().lower())
        if lab is None:
            unmapped[str(getattr(r, label_col))] += 1; continue
        dst = os.path.join(out_dir, f"{key}_{lab[:3]}.wav")
        if not os.path.exists(dst):
            cmd = [ff, "-v", "error", "-y", "-i", src, "-vn",
                   "-ac", "1", "-ar", str(sr), "-acodec", "pcm_s16le", dst]
            if subprocess.run(cmd, capture_output=True).returncode != 0 or \
               not os.path.exists(dst) or os.path.getsize(dst) < 2000:
                bad += 1
                if os.path.exists(dst): os.remove(dst)
                continue
        rows.append({"emotion": lab, "path": os.path.basename(dst), "clip": key})
        if (i + 1) % 100 == 0:
            print(f"  {i+1:,}/{len(items):,}  (추출 {len(rows):,})", flush=True)

    if not rows: sys.exit("추출된 클립이 없습니다. --id-col / --label-col 을 확인하세요.")
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "segments.csv"), index=False, encoding="utf-8-sig")

    print(f"\n[완료] {len(df):,}개 -> {out_dir}")
    if miss: print(f"  mp4 없음 {miss:,}")
    if bad:  print(f"  추출 실패(무음/코덱) {bad:,}")
    if unmapped: print(f"  매핑 안 된 라벨: {dict(unmapped.most_common(8))}")
    print("\n라벨 분포:")
    print(df.emotion.value_counts().to_string())
    print(f"\n다음:\n  python src/eval_external.py --ckpt work/ckpt/pilot_1006/best.pt "
          f"--dir \"{out_dir}\" --csv segments.csv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="kagglehub 가 내려받은 경로")
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--out", default=None, help="wav 를 저장할 폴더")
    ap.add_argument("--label-csv", default=None)
    ap.add_argument("--id-col", default=None)
    ap.add_argument("--label-col", default=None)
    ap.add_argument("--sr", type=int, default=16000)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if not os.path.isdir(args.root): sys.exit(f"폴더가 없습니다: {args.root}")
    if not args.extract:
        inspect(args.root); return
    for need in ("label_csv", "id_col", "label_col"):
        if not getattr(args, need):
            sys.exit(f"--{need.replace('_','-')} 가 필요합니다. 먼저 --extract 없이 실행해 구조를 확인하세요.")
    out = args.out or os.path.join(os.path.expanduser("~"), "Desktop", "kerc_audio")
    extract(args.root, out, args.label_csv, args.id_col, args.label_col, args.sr, args.limit)


if __name__ == "__main__":
    main()
