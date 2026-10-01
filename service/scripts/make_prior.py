# -*- coding: utf-8 -*-
"""
로짓 보정용 prior.json 만들기.

로짓 보정이란: 학습 데이터에 많았던 감정 쪽으로 모델이 쏠리는 걸, 그 비율로 나눠서 펴주는 것.
  보정된 로짓 = 로짓 − τ · log(학습 비율)
τ 는 검증셋에서만 고르고 테스트에는 한 번만 적용한다 (테스트로 고르면 반칙).

사용법
  1) 학습 매니페스트에서 바로:
     python scripts/make_prior.py --manifest ../ser/work/manifest_split_mix.csv --tau 0.6 \
            --out ../ser/work/ckpt/mix40k/prior.json
  2) 개수를 직접 줄 때:
     python scripts/make_prior.py --counts angry=13146,sadness=19976,... --tau 0.6 --out prior.json

만들어진 prior.json 을 체크포인트(best.pt) 와 같은 폴더에 두면
api/ser/infer.py 가 모델을 올릴 때 자동으로 읽어 적용한다.
"""
import argparse, csv, collections, json, math, os

CLASSES = ["angry", "sadness", "happy", "neutral", "fear", "disgust", "surprise"]


def from_manifest(path, split="train"):
    c = collections.Counter()
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("split") == split and row.get("label"):
                c[row["label"]] += 1
    return dict(c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest")
    ap.add_argument("--split", default="train")
    ap.add_argument("--counts", help="angry=100,sadness=200,... 형식")
    ap.add_argument("--tau", type=float, default=0.6)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    if a.manifest:
        counts = from_manifest(a.manifest, a.split)
    elif a.counts:
        counts = {k: float(v) for k, v in (kv.split("=") for kv in a.counts.split(","))}
    else:
        ap.error("--manifest 나 --counts 중 하나는 있어야 해")

    missing = [c for c in CLASSES if c not in counts]
    if missing:
        raise SystemExit(f"빠진 감정이 있어: {missing}")

    tot = sum(counts.values())
    print(f"{'감정':<9}{'개수':>9}{'비율':>8}{'보정 배수':>11}")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        p = v / tot
        print(f"{k:<9}{int(v):>9,}{p*100:>7.1f}%{math.exp(-a.tau*math.log(p)):>10.2f}×")

    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    json.dump({"tau": a.tau, "prior": counts,
               "note": f"train 분포 {int(tot):,}개 · tau 는 val 에서 선택"},
              open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n저장: {a.out}  (체크포인트와 같은 폴더에 두면 자동 적용)")


if __name__ == "__main__":
    main()
