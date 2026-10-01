# -*- coding: utf-8 -*-
"""0단계: EDA 리포트 — 학습 전에 반드시 한 번 돌려서 함정 확인
python src/eda_report.py --config configs/base.yaml --out work/eda
"""
import argparse, os, sys
from collections import Counter
import numpy as np, pandas as pd, yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_manifest import read_csv_any, NORM, EMO_COLS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/base.yaml")
    ap.add_argument("--out", default="work/eda")
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    os.makedirs(args.out, exist_ok=True)
    raw = cfg["paths"]["raw_root"]

    fr = []
    for src, name in cfg["paths"]["csv"].items():
        d = read_csv_any(os.path.join(raw, name))
        d.columns = [c.strip() for c in d.columns]
        if list(d.columns)[:2] == ["wav_id", "wav_id"]:
            c = list(d.columns); c[1] = "발화문"; d.columns = c
        d["src"] = src; fr.append(d)
    df = pd.concat(fr, ignore_index=True)
    for c in EMO_COLS:
        df[c] = df[c].astype(str).str.lower().str.strip().map(lambda x: NORM.get(x, x))
    df["scenario"] = df["상황"].astype(str).str.lower().str.strip().map(lambda x: NORM.get(x, x))
    v = df[EMO_COLS].apply(Counter, axis=1)
    df["maj"] = v.map(lambda c: c.most_common(1)[0][0])
    df["nvote"] = v.map(lambda c: c.most_common(1)[0][1])
    df["spk"] = df.src + "_" + df["나이"].astype(str) + "_" + df["성별"].astype(str)

    lines = []
    def P(*a):
        s = " ".join(str(x) for x in a); print(s); lines.append(s)

    P(f"# EDA 리포트  (총 {len(df):,}행, wav_id 고유 {df.wav_id.nunique():,})\n")
    P("## 1. 라벨 신뢰도 — '상황' 컬럼을 왜 버려야 하는가")
    P(f"시나리오(상황) vs 평가자 다수결 일치율: {(df.scenario==df.maj).mean():.3f}")
    P(pd.crosstab(df.scenario, df.maj, normalize='index').round(2).to_string())
    P("\n## 2. 평가자 합의 강도 (5명 중 최다 득표)")
    P(df.nvote.value_counts().sort_index().to_string())
    P("\n## 3. 클래스 불균형 (다수결 기준)")
    c = df.maj.value_counts(); P(c.to_string()); P(f"불균형비 {c.max()/c.min():.1f}:1")
    P("\n## 4. 화자 편중 — 랜덤 split 금지 근거")
    g = df.groupby("spk").size().sort_values(ascending=False)
    P(f"화자 그룹 {len(g)}개, 상위 2개가 전체의 {g.head(2).sum()/len(df)*100:.1f}%")
    P(g.head(10).to_string())
    P("\n## 5. 소스별 클래스 커버리지 — 도메인 누수 위험")
    P(pd.crosstab(df.src, df.scenario).to_string())
    P("\n## 6. 성별/나이 편중")
    P(df["성별"].value_counts().to_string())
    P(df["나이"].describe().round(1).to_string())
    P("\n## 7. 텍스트 중복 (같은 문장이 train/test 양쪽에 갈 위험)")
    d = df["발화문"].astype(str).duplicated(keep=False)
    P(f"중복행 {d.sum():,} / 고유 중복문장 {df.loc[d,'발화문'].nunique():,}")

    open(os.path.join(args.out, "eda_report.md"), "w", encoding="utf-8").write("\n".join(lines))
    df.to_csv(os.path.join(args.out, "merged_raw.csv"), index=False, encoding="utf-8-sig")
    print(f"\n[saved] {args.out}/eda_report.md")


if __name__ == "__main__":
    main()
