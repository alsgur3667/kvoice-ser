# -*- coding: utf-8 -*-
"""분할 끝난 manifest 여러 개를 하나로 합친다 (도메인 혼합 학습용).

왜 이런 게 필요한가:
  AI-Hub(대화체, 화자 111그룹, 평가자 5명 투표)와
  SKT(낭독체, 화자 8명, 연기 지시 라벨)는 성격이 완전히 다르다.
  SKT 만으로 이어서 학습하면 모델이 그쪽으로 끌려가 AI-Hub 성능을 까먹는다
  (catastrophic forgetting). 둘을 섞어서 같이 보여줘야 한다.

두 가지 원칙을 코드로 강제한다:
  1) 판정은 base 의 test 로만 한다.
     add 쪽 데이터는 train 으로만 들어간다. add 의 val/test 는 버린다.
     그래야 "SKT 에 과적합된 모델이 좋아 보이는" 착시가 생기지 않는다.
  2) add 를 무제한 넣지 않는다.
     SKT 15만 vs AI-Hub 2.5만이면 AI-Hub 가 묻힌다. --add-max 로 제한하고,
     (화자 x 라벨) 그룹을 돌아가며 뽑아 화자와 클래스가 한쪽으로 쏠리지 않게 한다.

  python src/merge_manifest.py \
      --base work/manifest_split.csv \
      --add  work/manifest_split_skt.csv --add-max 40000 \
      --out  work/manifest_split_mix.csv
"""
import argparse, os, sys
import numpy as np, pandas as pd


def balanced_take(df, n, seed=42, by=("spk", "label")):
    """(화자 x 라벨) 그룹을 라운드로빈으로 돌며 n 개를 뽑는다.
    단순 무작위로 뽑으면 많은 화자/흔한 클래스가 그대로 지배한다."""
    if n is None or n >= len(df):
        return df
    rng = np.random.RandomState(seed)
    groups = [g.sample(frac=1.0, random_state=rng.randint(1 << 30))
              for _, g in df.groupby(list(by), sort=True)]
    picked, i = [], 0
    while len(picked) < n and any(len(g) > i for g in groups):
        for g in groups:
            if i < len(g):
                picked.append(g.iloc[[i]])
                if len(picked) >= n:
                    break
        i += 1
    return pd.concat(picked).reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="기준 manifest. split 을 그대로 유지한다")
    ap.add_argument("--add", action="append", default=[], help="추가 manifest. 여러 번 쓸 수 있다")
    ap.add_argument("--add-max", action="append", default=[], type=int,
                    help="--add 각각의 최대 행 수. 생략하면 제한 없음")
    ap.add_argument("--add-splits", default="train",
                    help="추가 manifest 에서 가져올 split. 쉼표 구분. 기본 train")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if not os.path.exists(args.base):
        sys.exit(f"[FAIL] 없는 파일: {args.base}")
    base = pd.read_csv(args.base)
    print(f"[base] {args.base}  {len(base):,}행")
    print(base.split.value_counts().to_string(), "\n")

    want = [x.strip() for x in args.add_splits.split(",") if x.strip()]
    parts = [base]
    for i, p in enumerate(args.add):
        if not os.path.exists(p):
            sys.exit(f"[FAIL] 없는 파일: {p}")
        a = pd.read_csv(p)
        cap = args.add_max[i] if i < len(args.add_max) else None
        n0 = len(a)
        a = a[a.split.isin(want)]
        n1 = len(a)
        a = balanced_take(a, cap, seed=args.seed)
        a = a.copy()
        a["split"] = "train"          # 원칙 1: 추가분은 무조건 train
        print(f"[add {i+1}] {p}")
        print(f"  {n0:,}행 -> split{want} {n1:,}행 -> 상한 적용 {len(a):,}행")
        if "src" in a.columns:
            print("  출처:", dict(a.src.value_counts()))
        print("  화자:", a.spk.nunique(), "명 ·", dict(a.label.value_counts()), "\n")
        parts.append(a)

    # 열을 맞춘다. 한쪽에만 있는 열은 비워 둔다(어느 쪽인지 알 수 있게).
    cols = list(base.columns)
    extra = [c for pt in parts[1:] for c in pt.columns if c not in cols]
    for c in dict.fromkeys(extra):
        cols.append(c)
    parts = [pt.reindex(columns=cols) for pt in parts]

    mix = pd.concat(parts, ignore_index=True)

    dup = mix.wav_id.duplicated().sum()
    if dup:
        print(f"[warn] wav_id 중복 {dup:,}건 -> 뒤에 온 것을 버립니다")
        mix = mix.drop_duplicates("wav_id", keep="first").reset_index(drop=True)

    miss = mix.cache_path.isna().sum() if "cache_path" in mix.columns else len(mix)
    if miss:
        sys.exit(f"[FAIL] cache_path 가 없는 행 {miss:,}개. "
                 "합치기 전에 각 manifest 로 preprocess_audio.py 를 먼저 돌리세요.")

    mix.to_csv(args.out, index=False, encoding="utf-8-sig")
    print("=" * 66)
    print(f"[saved] {args.out}  {len(mix):,}행")
    print("\n[split]\n", mix.split.value_counts().to_string())
    print("\n[split x src]\n", pd.crosstab(mix.split, mix.src))
    print("\n[train 의 라벨 분포]")
    tr = mix[mix.split == "train"]
    vc = tr.label.value_counts()
    for k, v in vc.items():
        print(f"  {k:<10} {v:>8,}  {v/len(tr)*100:5.1f}%")
    print(f"  불균형비 {vc.max()/max(vc.min(),1):.1f}:1")
    if "src" in tr.columns:
        print("\n[train 의 출처 비율]")
        for k, v in tr.src.value_counts().items():
            print(f"  {k:<14} {v:>8,}  {v/len(tr)*100:5.1f}%")
    print("\n  주의: 성능 판정은 이 파일의 test(= base 의 test)로만 합니다.")
    print("=" * 66)


if __name__ == "__main__":
    main()
