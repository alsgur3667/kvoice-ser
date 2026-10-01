# -*- coding: utf-8 -*-
"""
1단계: CSV 3개 -> 학습용 manifest.csv

핵심 설계 (여기가 정확도의 8할):
  * '상황' 컬럼(연기 지시용 시나리오 감정)은 라벨로 쓰지 않는다.
    - 평가자 다수결과 68%만 일치 = 32%는 "슬프게 연기했지만 아무도 슬프게 안 들림".
    - 상황을 라벨로 쓰면 애초에 배울 수 없는 걸 배우라고 시키는 꼴.
  * 라벨 = 평가자 5명의 다수결(hard) + 투표분포(soft).
  * 발화문(텍스트), 감정세기는 manifest에서 제외 -> 오디오만으로 학습.
  * 화자 그룹(spk)을 만들어 speaker-independent split 에 쓴다.

사용:  python src/build_manifest.py --config configs/base.yaml
"""
import argparse, os, sys, json
from collections import Counter
import numpy as np
import pandas as pd
import yaml

NORM = {
    "anger": "angry", "angry": "angry",
    "sad": "sadness", "sadness": "sadness",
    "happiness": "happy", "happy": "happy",
    "disgust": "disgust", "fear": "fear",
    "surprise": "surprise", "neutral": "neutral",
}
EMO_COLS = ["1번 감정", "2번 감정", "3번 감정", "4번 감정", "5번 감정"]


def read_csv_any(path):
    """AI-Hub 배포본은 cp949. utf-8 로 재저장된 경우도 대비."""
    for enc in ("cp949", "utf-8-sig", "utf-8"):
        try:
            return pd.read_csv(path, encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise RuntimeError(f"인코딩 판별 실패: {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/base.yaml")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))

    raw = cfg["paths"]["raw_root"]
    work = cfg["paths"]["work_root"]
    os.makedirs(work, exist_ok=True)
    classes = cfg["label"]["classes"]

    rows = []
    for src, csv_name in cfg["paths"]["csv"].items():
        df = read_csv_any(os.path.join(raw, csv_name))
        df.columns = [c.strip() for c in df.columns]
        # 일부 배포본은 첫 컬럼명이 wav_id 로 중복되어 있음 -> 위치 기준 보정
        if list(df.columns)[:2] == ["wav_id", "wav_id"]:
            cols = list(df.columns); cols[1] = "발화문"; df.columns = cols
        df["src"] = src
        df["wav_path"] = df["wav_id"].astype(str).map(
            lambda i: os.path.join(raw, cfg["paths"]["wav_subdir"][src], f"{i}.wav")
        )
        rows.append(df)
    df = pd.concat(rows, ignore_index=True)
    print(f"[load] 총 {len(df):,}행 / wav_id 고유 {df.wav_id.nunique():,}")

    # ---- 평가자 라벨 정규화 ----
    for c in EMO_COLS:
        df[c] = df[c].astype(str).str.lower().str.strip().map(lambda x: NORM.get(x, x))
    bad = set(pd.unique(df[EMO_COLS].values.ravel())) - set(NORM.values())
    if bad:
        print(f"[warn] 미정의 라벨 발견(제외됨): {bad}")

    votes = df[EMO_COLS].apply(Counter, axis=1)
    df["maj"] = votes.map(lambda c: c.most_common(1)[0][0])
    df["n_votes"] = votes.map(lambda c: c.most_common(1)[0][1])
    df["is_tie"] = votes.map(
        lambda c: sum(1 for v in c.values() if v == c.most_common(1)[0][1]) > 1
    )
    # soft label (투표 분포)
    soft = np.array([[c.get(k, 0) / len(EMO_COLS) for k in classes] for c in votes])
    for i, k in enumerate(classes):
        df[f"p_{k}"] = soft[:, i]
    p = np.clip(soft, 1e-9, 1)
    df["entropy"] = -(soft * np.log(p)).sum(1)

    # ---- 화자 그룹 추정 ----
    # 이 데이터셋엔 speaker_id 가 없다. (소스, 나이, 성별) 조합이 사실상 화자 단위.
    # 완벽하진 않지만 랜덤 split 보다 압도적으로 정직한 평가를 준다.
    df["spk"] = df["src"] + "_" + df["나이"].astype(str) + "_" + df["성별"].astype(str)

    # ---- 시나리오 감정은 '메타'로만 보관 (학습 입력 아님) ----
    df["scenario"] = df["상황"].astype(str).str.lower().str.strip().map(lambda x: NORM.get(x, x))

    # ---- 필터링 ----
    n0 = len(df)
    df = df[df["maj"].isin(classes)]
    if cfg["label"]["drop_tie"]:
        df = df[~df["is_tie"]]
    df = df[df["n_votes"] >= cfg["label"]["min_votes"]]
    print(f"[filter] {n0:,} -> {len(df):,} (동점/저합의 제거)")

    # ---- 실제 파일 존재 확인 ----
    exists = df["wav_path"].map(os.path.exists)
    if (~exists).any():
        print(f"[warn] wav 없음 {(~exists).sum():,}개 제외")
        print(df.loc[~exists, "wav_path"].head(3).tolist())
    df = df[exists]

    keep = ["wav_id", "wav_path", "src", "spk", "나이", "성별",
            "maj", "n_votes", "entropy", "scenario"] + [f"p_{k}" for k in classes]
    out = df[keep].rename(columns={"나이": "age", "성별": "gender", "maj": "label"})
    path = args.out or os.path.join(work, "manifest.csv")
    out.to_csv(path, index=False, encoding="utf-8-sig")

    print(f"\n[saved] {path}  ({len(out):,}행)")
    print("\n라벨 분포:\n", out.label.value_counts())
    print(f"\n불균형비 {out.label.value_counts().max()/out.label.value_counts().min():.1f}:1")
    print(f"화자 그룹 수: {out.spk.nunique()}")
    print("\n시나리오 vs 다수결 일치율: "
          f"{(out.scenario == out.label).mean():.3f}   <- 이게 '상황' 컬럼을 버리는 이유")


if __name__ == "__main__":
    main()
