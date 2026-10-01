# -*- coding: utf-8 -*-
"""
3단계: 화자 독립(speaker-independent) 분할

왜 중요한가 — 이 데이터셋의 최대 함정:
  화자 그룹이 111개뿐인데 상위 2명이 전체의 22%를 차지한다.
  랜덤 split 하면 같은 화자의 목소리가 train/test 양쪽에 들어가서
  모델이 '감정'이 아니라 '이 사람 목소리'를 외운다 -> 검증 90%, 실서비스 45%.
  화자 단위로 쪼개면 검증 점수는 떨어지지만 그게 진짜 성능이다.

추가 방어:
  * 발화문 중복 8,466행(고유 1,687문장) -> 같은 문장이 양쪽에 가지 않게 그룹화 가능
  * happy/surprise 는 5차년도_2차 에만 존재 -> 소스 편중 리포트 출력

사용: python src/split.py --config configs/base.yaml
"""
import argparse, os
import numpy as np, pandas as pd, yaml
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from wpath import wp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/base.yaml")
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    work = cfg["paths"]["work_root"]
    s = cfg["split"]
    rng = np.random.RandomState(s["seed"])

    df = pd.read_csv(wp(cfg, "manifest_proc.csv"))

    # 화자를 직접 지정하는 모드.
    # 화자가 8명뿐인 SKT 같은 코퍼스에서는 비율 기반 자동 분할이 무의미하다
    # (한 명이 12.5%씩이라 '큰 화자' 규칙에 전원이 걸려 pool 이 비어버린다).
    # 누가 test 로 가는지를 사람이 정하고 문서에 남기는 게 정직하다.
    if s["mode"] == "speaker_list":
        te = [str(x) for x in s.get("test_speakers", [])]
        va = [str(x) for x in s.get("val_speakers", [])]
        have = set(df.spk.astype(str))
        miss = (set(te) | set(va)) - have
        if miss:
            raise SystemExit(f"manifest 에 없는 화자: {sorted(miss)}\n있는 화자: {sorted(have)}")
        if set(te) & set(va):
            raise SystemExit(f"test 와 val 에 같은 화자가 있습니다: {sorted(set(te)&set(va))}")
        df["split"] = np.select(
            [df.spk.astype(str).isin(te), df.spk.astype(str).isin(va)],
            ["test", "val"], default="train")
        tr = sorted(have - set(te) - set(va))
        if not tr:
            raise SystemExit("train 에 남는 화자가 없습니다")
        df.to_csv(wp(cfg, "manifest_split.csv"), index=False, encoding="utf-8-sig")
        print("[화자 지정]")
        print(f"  train {len(tr)}명: {', '.join(tr)}")
        print(f"  val   {len(va)}명: {', '.join(va)}")
        print(f"  test  {len(te)}명: {', '.join(te)}")
        print("\n[샘플 수]\n", df.split.value_counts())
        print("\n[split x label]\n", pd.crosstab(df.split, df.label))
        for sp in ["val", "test"]:
            missc = set(cfg["label"]["classes"]) - set(df[df.split == sp].label.unique())
            if missc:
                print(f"[warn] {sp}에 없는 클래스: {missc}")
        print(f"\n[saved] {wp(cfg, 'manifest_split.csv')}")
        return

    if s["mode"] != "speaker":
        raise SystemExit("랜덤 분할은 이 데이터셋에서 성능을 심각하게 부풀립니다. speaker 유지하세요.")

    # 화자별 크기/클래스 커버리지
    spk = df.groupby("spk").agg(n=("label", "size"), ncls=("label", "nunique")).reset_index()
    # 큰 화자는 train 에 고정(테스트가 특정 대형화자에 지배당하지 않게)
    spk = spk.sort_values("n", ascending=False)
    big = spk[spk.n > len(df) * 0.05].spk.tolist()
    pool = spk[~spk.spk.isin(big)].spk.tolist()
    rng.shuffle(pool)

    n_test = max(1, int(len(pool) * s["test_speaker_ratio"] / (1 - 0.0)))
    n_val = max(1, int(len(pool) * s["val_speaker_ratio"]))
    test_spk, val_spk = pool[:n_test], pool[n_test:n_test + n_val]
    train_spk = big + pool[n_test + n_val:]

    df["split"] = np.select(
        [df.spk.isin(test_spk), df.spk.isin(val_spk)], ["test", "val"], default="train")

    df.to_csv(wp(cfg, "manifest_split.csv"), index=False, encoding="utf-8-sig")

    print("[화자 수]", {k: len(v) for k, v in
                      dict(train=train_spk, val=val_spk, test=test_spk).items()})
    print("\n[샘플 수]\n", df.split.value_counts())
    print("\n[split x label]\n", pd.crosstab(df.split, df.label))
    print("\n[split x src]\n", pd.crosstab(df.split, df.src))
    for sp in ["val", "test"]:
        miss = set(cfg["label"]["classes"]) - set(df[df.split == sp].label.unique())
        if miss:
            print(f"[warn] {sp}에 없는 클래스: {miss} -> seed 바꾸거나 화자 수동 배정 필요")
    assert not (set(train_spk) & set(test_spk)), "화자 누수!"
    print(f"\n[saved] {wp(cfg, 'manifest_split.csv')}")


if __name__ == "__main__":
    main()
