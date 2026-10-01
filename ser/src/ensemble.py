# -*- coding: utf-8 -*-
"""
앙상블 — 서로 다른 모델의 확률을 섞어 둘 다 이긴다.

WavLM 파인튜닝은 재현율이, emotion2vec_base 프리즈는 정밀도가 높다.
성격이 다른 두 모델을 섞으면 보통 둘 다보다 좋아진다. 추가 학습은 없다.

준비: 각 실험의 eval_test.csv 에 prob_* 컬럼이 있어야 한다.
      (evaluate.py / e2v_train.py 를 최신 버전으로 한 번 더 돌리면 생긴다)

  python src/ensemble.py --runs pilot_1006 e2v_base_cbf
  python src/ensemble.py                      # work/ckpt 아래 가능한 것 전부
"""
import argparse, os, sys, glob, itertools
import numpy as np, pandas as pd
from sklearn.metrics import (recall_score, accuracy_score, f1_score,
                             confusion_matrix, classification_report)


def load(work, run):
    f = os.path.join(work, "ckpt", run, "eval_test.csv")
    if not os.path.exists(f): return None
    d = pd.read_csv(f)
    pc = [c for c in d.columns if c.startswith("prob_")]
    if not pc: return None
    d["wid"] = d.wav_id.astype(str)
    return d.set_index("wid"), [c[5:] for c in pc]


def score(y, p, classes):
    L = list(range(len(classes)))
    return (recall_score(y, p, labels=L, average="macro", zero_division=0),
            accuracy_score(y, p),
            f1_score(y, p, labels=L, average="macro", zero_division=0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="./work")
    ap.add_argument("--runs", nargs="*", default=None)
    args = ap.parse_args()

    runs = args.runs or sorted(
        os.path.basename(os.path.dirname(f))
        for f in glob.glob(os.path.join(args.work, "ckpt", "*", "eval_test.csv")))

    loaded, classes = {}, None
    for r in runs:
        got = load(args.work, r)
        if got is None:
            print(f"[skip] {r} — prob_* 컬럼 없음 (평가를 다시 돌리세요)"); continue
        d, cl = got
        if classes is None: classes = cl
        elif cl != classes: print(f"[skip] {r} — 클래스 순서가 다름"); continue
        loaded[r] = d
        print(f"[load] {r}  n={len(d):,}")

    if len(loaded) < 2:
        sys.exit("\n앙상블하려면 prob_* 를 가진 실험이 2개 이상 필요합니다.\n"
                 "  python src/evaluate.py --ckpt work/ckpt/<run>/best.pt --split test\n"
                 "  를 각 실험에 대해 다시 돌리세요.")

    # 공통 샘플만
    ids = set.intersection(*[set(d.index) for d in loaded.values()])
    ids = sorted(ids)
    print(f"\n[공통] {len(ids):,}개 샘플")
    c2i = {c: i for i, c in enumerate(classes)}
    base = next(iter(loaded.values())).loc[ids]
    y = base.label.map(c2i).values
    P = {r: d.loc[ids][[f"prob_{c}" for c in classes]].values for r, d in loaded.items()}

    print("\n=== 단일 모델 ===")
    singles = {}
    for r, pr in P.items():
        u, a, f = score(y, pr.argmax(1), classes)
        singles[r] = u
        print(f"  {r:22s} UAR {u:.4f}  WAR {a:.4f}  F1 {f:.4f}")

    names = list(P)
    print("\n=== 2개 조합 · 가중치 탐색 ===")
    best = None
    for r1, r2 in itertools.combinations(names, 2):
        rows = []
        for w in np.arange(0, 1.01, 0.05):
            mix = w * P[r1] + (1 - w) * P[r2]
            u, a, f = score(y, mix.argmax(1), classes)
            rows.append((w, u, a, f))
        w, u, a, f = max(rows, key=lambda t: t[1])
        gain = u - max(singles[r1], singles[r2])
        mark = "  <== 개선" if gain > 0.005 else ""
        print(f"  {r1[:18]:18s} x {r2[:18]:18s}  w={w:.2f}  "
              f"UAR {u:.4f} ({gain:+.4f})  WAR {a:.4f}  F1 {f:.4f}{mark}")
        if best is None or u > best[1]:
            best = ((r1, r2), u, a, f, w)

    if len(names) >= 3:
        mix = sum(P.values()) / len(P)
        u, a, f = score(y, mix.argmax(1), classes)
        print(f"\n  전체 균등 평균 ({len(names)}개)      UAR {u:.4f}  WAR {a:.4f}  F1 {f:.4f}")
        if u > best[1]: best = (tuple(names), u, a, f, None)

    (r1r2, u, a, f, w) = best
    print("\n" + "=" * 70)
    print(f"최고 조합: {' + '.join(r1r2)}" + (f"  (가중치 {w:.2f} / {1-w:.2f})" if w is not None else ""))
    print(f"  UAR {u:.4f}   WAR {a:.4f}   macroF1 {f:.4f}")
    print("=" * 70)

    if w is not None:
        mix = w * P[r1r2[0]] + (1 - w) * P[r1r2[1]]
    else:
        mix = sum(P[r] for r in r1r2) / len(r1r2)
    pred = mix.argmax(1)
    print("\n" + classification_report(y, pred, labels=list(range(len(classes))),
                                       target_names=classes, digits=3, zero_division=0))
    cm = confusion_matrix(y, pred, labels=list(range(len(classes))))
    print("혼동행렬 (행=정답, 행정규화 %)")
    print(pd.DataFrame((cm / np.maximum(cm.sum(1, keepdims=True), 1) * 100).round(1),
                       index=classes, columns=classes).to_string())

    conf = mix.max(1) / np.maximum(mix.sum(1), 1e-9)
    ok = (pred == y).astype(float)
    print("\n[임계값별 커버리지 / 정확도]")
    for th in (0.5, 0.6, 0.7, 0.8, 0.9):
        m = conf >= th
        if m.sum(): print(f"  >= {th:.1f} : 커버리지 {m.mean():6.1%}  정확도 {ok[m].mean():6.1%}")

    out = os.path.join(args.work, "ensemble_test.csv")
    pd.DataFrame({"wav_id": ids, "label": base.label.values,
                  "pred": [classes[i] for i in pred], "conf": conf,
                  **{f"prob_{c}": mix[:, i] for i, c in enumerate(classes)}}
                 ).to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\n[saved] {out}")


if __name__ == "__main__":
    main()
