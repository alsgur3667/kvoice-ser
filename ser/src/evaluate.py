# -*- coding: utf-8 -*-
"""7단계: 테스트 평가 + 혼동행렬 + 화자/성별별 성능 + 신뢰도 보정"""
import argparse, os, sys, json
import numpy as np, pandas as pd, torch, yaml
from torch.utils.data import DataLoader
from sklearn.metrics import (classification_report, confusion_matrix,
                             recall_score, f1_score, accuracy_score)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wpath import wp
from dataset import SERDataset, collate
from model import SERModel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--split", default="test",
                    help='test | val | train | all ("all"은 분할 무시하고 전체)')
    ap.add_argument("--manifest", default=None,
                    help="다른 manifest 로 평가한다. 교차 코퍼스 검증용. "
                         "예: work/manifest_split_skt.csv --split all")
    ap.add_argument("--tb", action="store_true",
                    help="결과를 TensorBoard 로도 기록 (work/tb/<run>_eval)")
    args = ap.parse_args()
    ck = torch.load(args.ckpt, map_location="cpu", weights_only=False)
    cfg = ck["cfg"]; classes = cfg["label"]["classes"]
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    mani = args.manifest or wp(cfg, "manifest_split.csv")
    print(f"[manifest] {mani}")
    df = pd.read_csv(mani)
    if args.split != "all" and "split" not in df.columns:
        raise SystemExit(f"{mani} 에 split 컬럼이 없습니다. --split all 을 쓰세요.")
    ds = SERDataset(df, cfg, args.split)
    dl = DataLoader(ds, batch_size=16, collate_fn=collate, num_workers=4)

    model = SERModel(cfg); model.load_state_dict(ck["model"]); model.to(dev).eval()
    P, Y, C, R = [], [], [], []
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
        for b in dl:
            lo = model(b["input_values"].to(dev), b["attention_mask"].to(dev)).float()
            pr = torch.softmax(lo, -1).cpu()
            P.append(pr.argmax(-1)); C.append(pr.max(-1).values); Y.append(b["y"])
            R.append(pr)
    p, y, c = torch.cat(P).numpy(), torch.cat(Y).numpy(), torch.cat(C).numpy()
    PROB = torch.cat(R).numpy()

    print(f"\n=== {args.split} (n={len(y):,}) ===")
    L = list(range(len(classes)))
    print(f"UAR {recall_score(y,p,labels=L,average='macro',zero_division=0):.4f}   "
          f"WAR {accuracy_score(y,p):.4f}   "
          f"macroF1 {f1_score(y,p,labels=L,average='macro',zero_division=0):.4f}")
    # labels 를 명시해야 테스트셋에 없는 클래스가 있어도 리포트가 깨지지 않는다
    print("\n", classification_report(y, p, labels=list(range(len(classes))),
                                      target_names=classes, digits=3, zero_division=0))

    cm = confusion_matrix(y, p, labels=range(len(classes)))
    print("혼동행렬 (행=정답, 열=예측, 행정규화 %)")
    print(pd.DataFrame((cm / cm.sum(1, keepdims=True).clip(1) * 100).round(1),
                       index=classes, columns=classes))

    sub = ds.df.copy(); sub["pred"] = [classes[i] for i in p]; sub["conf"] = c
    sub["correct"] = sub.pred == sub.label
    for i, cl in enumerate(classes):          # 앙상블용 클래스별 확률
        sub[f"prob_{cl}"] = PROB[:, i]
    print("\n[성별별 정확도]\n", sub.groupby("gender").correct.mean().round(3))
    print("\n[화자별 정확도 (하위 5)]\n",
          sub.groupby("spk").correct.agg(["mean", "size"]).sort_values("mean").head(5).round(3))
    # 신뢰도 구간별 정확도 = 서비스에서 '모름' 처리 임계값 잡는 근거
    sub["bin"] = pd.cut(sub.conf, [0, .5, .6, .7, .8, .9, 1.0])
    print("\n[신뢰도별 정확도/비중]\n",
          sub.groupby("bin", observed=True).agg(acc=("correct", "mean"),
                                                n=("correct", "size")).round(3))
    out = os.path.join(os.path.dirname(args.ckpt), f"eval_{args.split}.csv")
    sub.to_csv(out, index=False, encoding="utf-8-sig"); print(f"\n[saved] {out}")

    if args.tb:
        write_tb(args, cfg, classes, y, p, c, cm, sub)


def write_tb(args, cfg, classes, y, p, c, cm, sub):
    """학습 곡선이 없는 예전 체크포인트라도, 평가 결과는 TensorBoard 로 볼 수 있게 한다."""
    try:
        from torch.utils.tensorboard import SummaryWriter
    except Exception:
        print("[tb] tensorboard 미설치 — pip install tensorboard"); return
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import tb as tbviz
    from sklearn.metrics import precision_recall_fscore_support

    run = os.path.basename(os.path.dirname(args.ckpt))
    tb_dir = os.path.join(cfg["paths"]["work_root"], "tb", f"{run}_eval_{args.split}")
    w = SummaryWriter(tb_dir)

    L = list(range(len(classes)))
    pr, rc, f1, sup = precision_recall_fscore_support(y, p, labels=L, zero_division=0)
    w.add_scalar(f"{args.split}/UAR", recall_score(y, p, labels=L, average="macro", zero_division=0), 0)
    w.add_scalar(f"{args.split}/WAR_accuracy", accuracy_score(y, p), 0)
    w.add_scalar(f"{args.split}/macroF1", f1_score(y, p, labels=L, average="macro", zero_division=0), 0)
    for i, cl in enumerate(classes):
        w.add_scalar(f"{args.split}_precision/{cl}", pr[i], 0)
        w.add_scalar(f"{args.split}_recall/{cl}", rc[i], 0)
        w.add_scalar(f"{args.split}_f1/{cl}", f1[i], 0)

    rep = {cl: {"precision": pr[i], "recall": rc[i], "f1": f1[i], "support": int(sup[i])}
           for i, cl in enumerate(classes)}
    w.add_image(f"{args.split}/confusion",
                tbviz.confusion_figure(cm, classes, f"{args.split} confusion (row %)"), 0)
    w.add_image(f"{args.split}/per_class", tbviz.per_class_figure(rep, classes), 0)
    img, ece = tbviz.calibration_figure(sub.conf.values, sub.correct.values.astype(float))
    w.add_image(f"{args.split}/calibration", img, 0)
    w.add_scalar(f"{args.split}/ECE", ece, 0)

    # 임계값별 커버리지/정확도 곡선 — 서빙 임계값을 여기서 고른다
    for th in [i / 100 for i in range(30, 100, 5)]:
        m = sub.conf >= th
        if m.sum() == 0: continue
        w.add_scalar(f"{args.split}_threshold/coverage", m.mean(), int(th * 100))
        w.add_scalar(f"{args.split}_threshold/accuracy", sub.loc[m, "correct"].mean(), int(th * 100))

    rows = "| 클래스 | P | R | F1 | n |\n|---|---|---|---|---|\n" + "\n".join(
        f"| {cl} | {rep[cl]['precision']:.3f} | {rep[cl]['recall']:.3f} | "
        f"{rep[cl]['f1']:.3f} | {rep[cl]['support']} |" for cl in classes)
    w.add_text(f"{args.split}/report", rows, 0)
    try:   # to_markdown 은 tabulate 필요 — 없으면 건너뛴다
        w.add_text(f"{args.split}/speaker",
                   sub.groupby("spk").correct.agg(["mean", "size"])
                      .sort_values("mean").head(10).to_markdown(), 0)
    except Exception:
        pass
    w.close()
    print(f"[tb] {tb_dir}")
    print(f"     tensorboard --logdir {os.path.join(cfg['paths']['work_root'], 'tb')}")


if __name__ == "__main__":
    main()
