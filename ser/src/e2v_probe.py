# -*- coding: utf-8 -*-
"""
emotion2vec 특징 진단 — 특징이 나쁜가, 우리 헤드가 나쁜가?

헤드 학습 결과가 제로샷보다 낮게 나오면 둘 중 하나다.
  (A) 특징 자체가 한국어 감정을 잘 못 나눈다  -> 선형 프로브도 낮게 나옴
  (B) 헤드/손실 설정이 문제다               -> 선형 프로브가 훨씬 높게 나옴

선형 프로브는 SSL 표현 평가의 표준 프로토콜이라, 이 숫자가 논문에 비교 가능한 값이다.
GPU 불필요, 2~5분.

  python src/e2v_probe.py --config configs/pilot.yaml
"""
import argparse, os, sys, time
import numpy as np, pandas as pd, yaml
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import recall_score, accuracy_score, f1_score, confusion_matrix


def report(name, y, p, classes, t0):
    L = list(range(len(classes)))
    uar = recall_score(y, p, labels=L, average="macro", zero_division=0)
    acc = accuracy_score(y, p)
    f1 = f1_score(y, p, labels=L, average="macro", zero_division=0)
    print(f"  {name:34s} UAR {uar:.4f}   WAR {acc:.4f}   F1 {f1:.4f}   ({time.time()-t0:.0f}s)")
    return {"method": name, "uar": uar, "war": acc, "f1": f1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/pilot.yaml")
    ap.add_argument("--feats", default=None)
    ap.add_argument("--max-iter", type=int, default=2000)
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    work, classes = cfg["paths"]["work_root"], cfg["label"]["classes"]
    c2i = {c: i for i, c in enumerate(classes)}

    npz = np.load(args.feats or os.path.join(work, "e2v_feats.npz"), allow_pickle=True)
    fmap = dict(zip(npz["wav_id"].tolist(), npz["feats"]))
    print(f"[feats] {npz['feats'].shape[0]:,} × {npz['feats'].shape[1]}  ({str(npz['model'])})")

    df = pd.read_csv(os.path.join(work, "manifest_split.csv"))
    df["wid"] = df.wav_id.astype(str)
    df = df[df.wid.isin(fmap)]

    def pack(sp):
        d = df[df.split == sp]
        return np.stack([fmap[w] for w in d.wid]), d.label.map(c2i).values, d

    Xtr, ytr, _ = pack("train")
    Xte, yte, dte = pack("test")
    print(f"[split] train {len(ytr):,} / test {len(yte):,}  (화자 독립)")

    sc = StandardScaler().fit(Xtr)
    Xtr_s, Xte_s = sc.transform(Xtr), sc.transform(Xte)

    print(f"\n=== 선형 프로브 (SSL 표현 평가 표준) ===")
    rows = []
    for name, kw in [
        ("LogReg (가중 없음)",            dict(class_weight=None)),
        ("LogReg (class_weight=balanced)", dict(class_weight="balanced")),
    ]:
        t0 = time.time()
        clf = LogisticRegression(max_iter=args.max_iter, n_jobs=-1, **kw).fit(Xtr_s, ytr)
        rows.append(report(name, yte, clf.predict(Xte_s), classes, t0))

    t0 = time.time()
    knn = KNeighborsClassifier(n_neighbors=20, n_jobs=-1).fit(Xtr_s, ytr)
    rows.append(report("kNN (k=20)", yte, knn.predict(Xte_s), classes, t0))

    # 다수 클래스만 찍는 바보 기준선
    maj = np.bincount(ytr, minlength=len(classes)).argmax()
    rows.append(report("항상 다수 클래스 (바보 기준선)", yte,
                       np.full_like(yte, maj), classes, time.time()))

    print(f"\n  7클래스 랜덤 UAR = {1/7:.4f}")

    best = max(rows, key=lambda r: r["uar"])
    print(f"\n=== 진단 ===")
    print(f"  선형 프로브 최고 UAR: {best['uar']:.4f}  ({best['method']})")
    if best["uar"] > 0.45:
        print("  -> 특징은 쓸만한데 헤드/손실 설정이 문제입니다.")
        print("     e2v_train.py 를 --no-balance --loss ce 로 다시 돌려보세요.")
    elif best["uar"] > 0.35:
        print("  -> 특징이 어중간합니다. 헤드 튜닝으로 조금 오르겠지만 한계가 있습니다.")
    else:
        print("  -> 특징 자체가 한국어 감정을 잘 못 나눕니다.")
        print("     emotion2vec_plus_large 의 임베딩은 자체 분류기에 맞춰져 있어")
        print("     다른 데이터로 옮겨 쓰기 어려울 수 있습니다.")
        print("     SSL 원본으로 다시 추출해 보세요:")
        print("       e2v_extract.py --model emotion2vec/emotion2vec_base")

    # 혼동행렬 (최고 방법)
    clf = LogisticRegression(max_iter=args.max_iter, n_jobs=-1,
                             class_weight=None if "없음" in best["method"] else "balanced")
    clf.fit(Xtr_s, ytr)
    p = clf.predict(Xte_s)
    cm = confusion_matrix(yte, p, labels=list(range(len(classes))))
    print(f"\n혼동행렬 · {best['method']} (행=정답, 행정규화 %)")
    print(pd.DataFrame((cm / np.maximum(cm.sum(1, keepdims=True), 1) * 100).round(1),
                       index=classes, columns=classes).to_string())

    out = os.path.join(work, "e2v_probe.csv")
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\n[saved] {out}")


if __name__ == "__main__":
    main()
