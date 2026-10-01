# -*- coding: utf-8 -*-
"""
emotion2vec 특징 위에 분류기 학습 (2단계)

emotion2vec 논문의 다운스트림 프로토콜: 백본은 얼리고 그 위 헤드만 학습.
특징은 이미 .npz 로 뽑아놨으므로 GPU 없이도 몇 분이면 끝난다.
분할·손실·지표는 WavLM 실험과 **완전히 동일**해서 공정한 비교가 된다.

  python src/e2v_train.py --config configs/pilot.yaml
"""
import argparse, os, sys, time, math, json
import numpy as np, pandas as pd, yaml, torch
import torch.nn as nn, torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader, WeightedRandomSampler
from sklearn.metrics import (recall_score, f1_score, accuracy_score,
                             confusion_matrix, classification_report)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from losses import CBFocalLoss


class Head(nn.Module):
    """얼린 emotion2vec 임베딩 -> 7클래스"""
    def __init__(self, d_in, n_cls, hidden=512, dropout=0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(d_in),
            nn.Linear(d_in, hidden), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(hidden, hidden // 2), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(hidden // 2, n_cls))

    def forward(self, x): return self.net(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/pilot.yaml")
    ap.add_argument("--feats", default=None)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--run", default=None)
    ap.add_argument("--no-balance", action="store_true",
                    help="균형 샘플러 끄기 (희소 클래스 과예측이 심할 때)")
    ap.add_argument("--loss", default="cb_focal", choices=["cb_focal", "weighted_ce", "ce"],
                    help="ce = 가중 없음. 특징이 고정된 경우 오히려 나을 때가 많다")
    ap.add_argument("--hidden", type=int, default=512)
    ap.add_argument("--dropout", type=float, default=0.3)
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    work, classes = cfg["paths"]["work_root"], cfg["label"]["classes"]
    c2i = {c: i for i, c in enumerate(classes)}
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    npz_path = args.feats or os.path.join(work, "e2v_feats.npz")
    if not os.path.exists(npz_path):
        sys.exit(f"{npz_path} 가 없습니다. 먼저 e2v_extract.py 를 실행하세요.")
    z = np.load(npz_path, allow_pickle=True)
    feat_by_id = dict(zip(z["wav_id"].tolist(), z["feats"]))
    backbone = str(z["model"]) if "model" in z else "emotion2vec"
    print(f"[feats] {npz_path} · {z['feats'].shape[0]:,}개 × {z['feats'].shape[1]}차원")
    print(f"[model] {backbone}")

    df = pd.read_csv(os.path.join(work, "manifest_split.csv"))
    df["wid"] = df.wav_id.astype(str)
    df = df[df.wid.isin(feat_by_id)].reset_index(drop=True)
    soft_cols = [f"p_{c}" for c in classes]

    def pack(split):
        d = df[df.split == split]
        X = torch.tensor(np.stack([feat_by_id[w] for w in d.wid]), dtype=torch.float32)
        y = torch.tensor(d.label.map(c2i).values, dtype=torch.long)
        s = torch.tensor(d[soft_cols].values.astype(np.float32))
        return d, TensorDataset(X, y, s)

    d_tr, ds_tr = pack("train"); d_va, ds_va = pack("val"); d_te, ds_te = pack("test")
    print(f"[split] train {len(ds_tr):,} / val {len(ds_va):,} / test {len(ds_te):,} "
          f"(화자 독립)")

    # 표준화 (train 통계로만)
    mu = ds_tr.tensors[0].mean(0, keepdim=True)
    sd = ds_tr.tensors[0].std(0, keepdim=True).clamp_min(1e-6)
    for ds in (ds_tr, ds_va, ds_te):
        ds.tensors = ((ds.tensors[0] - mu) / sd, ds.tensors[1], ds.tensors[2])

    ylab = ds_tr.tensors[1].numpy()
    cnt = np.bincount(ylab, minlength=len(classes)).astype(float)
    sampler = None if args.no_balance else WeightedRandomSampler(
        torch.DoubleTensor((1.0 / np.maximum(cnt, 1))[ylab]), len(ylab), replacement=True)
    dl_tr = DataLoader(ds_tr, batch_size=args.batch, sampler=sampler,
                       shuffle=(sampler is None), drop_last=True)
    dl_va = DataLoader(ds_va, batch_size=512)
    dl_te = DataLoader(ds_te, batch_size=512)

    model = Head(ds_tr.tensors[0].shape[1], len(classes),
                 hidden=args.hidden, dropout=args.dropout).to(dev)
    sm = cfg["train"]["label_smoothing"]
    if args.loss == "cb_focal":
        hard_fn = CBFocalLoss(cnt, gamma=cfg["train"]["focal_gamma"], smoothing=sm).to(dev)
    elif args.loss == "weighted_ce":
        w = torch.tensor(cnt.sum() / np.maximum(cnt, 1), dtype=torch.float32)
        hard_fn = nn.CrossEntropyLoss(weight=(w / w.mean()).to(dev), label_smoothing=sm)
    else:
        hard_fn = nn.CrossEntropyLoss(label_smoothing=sm)
    print(f"[setup] loss={args.loss} · balanced_sampler={not args.no_balance} · "
          f"hidden={args.hidden} · dropout={args.dropout}")
    soft_w = cfg["label"]["soft_weight"] if cfg["label"]["use_soft_label"] else 0.0
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, args.epochs)

    run = args.run or f"e2v_{time.strftime('%m%d_%H%M')}"
    ckpt_dir = os.path.join(work, "ckpt", run); os.makedirs(ckpt_dir, exist_ok=True)
    writer = None
    try:
        from torch.utils.tensorboard import SummaryWriter
        writer = SummaryWriter(os.path.join(work, "tb", run))
    except Exception:
        pass

    def ev(loader):
        model.eval(); P, Y = [], []
        with torch.no_grad():
            for X, y, _ in loader:
                P.append(model(X.to(dev)).argmax(-1).cpu()); Y.append(y)
        p, y = torch.cat(P).numpy(), torch.cat(Y).numpy()
        L = list(range(len(classes)))
        return {"uar": recall_score(y, p, labels=L, average="macro", zero_division=0),
                "acc": accuracy_score(y, p),
                "f1": f1_score(y, p, labels=L, average="macro", zero_division=0)}

    best, bad = -1, 0
    print(f"\n[train] {args.epochs} epoch · lr {args.lr} · batch {args.batch}")
    for ep in range(args.epochs):
        model.train(); tot = 0.0
        for X, y, s in dl_tr:
            X, y, s = X.to(dev), y.to(dev), s.to(dev)
            lo = model(X)
            loss = (1 - soft_w) * hard_fn(lo, y)
            if soft_w > 0:
                loss = loss + soft_w * F.kl_div(F.log_softmax(lo, -1), s.clamp_min(1e-8),
                                                reduction="batchmean")
            opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
            tot += loss.item()
        sched.step()
        m = ev(dl_va)
        if writer:
            writer.add_scalar("train/loss_epoch", tot / len(dl_tr), ep)
            writer.add_scalar("val/UAR", m["uar"], ep)
            writer.add_scalar("val/WAR_accuracy", m["acc"], ep)
            writer.add_scalar("val/macroF1", m["f1"], ep)
        if (ep + 1) % 5 == 0 or ep == 0:
            print(f"  ep{ep:>3d}  loss {tot/len(dl_tr):.4f} | "
                  f"UAR {m['uar']:.4f}  WAR {m['acc']:.4f}  F1 {m['f1']:.4f}")
        if m["uar"] > best:
            best, bad = m["uar"], 0
            torch.save({"head": model.state_dict(), "mu": mu, "sd": sd,
                        "classes": classes, "backbone": backbone, "epoch": ep,
                        "d_in": ds_tr.tensors[0].shape[1]},
                       os.path.join(ckpt_dir, "head.pt"))
        else:
            bad += 1
            if bad >= 15: print(f"  early stop (ep{ep})"); break

    # ---- test ----
    model.load_state_dict(torch.load(os.path.join(ckpt_dir, "head.pt"),
                                     map_location=dev, weights_only=False)["head"])
    model.eval(); P, C, Y, R = [], [], [], []
    with torch.no_grad():
        for X, y, _ in dl_te:
            pr = torch.softmax(model(X.to(dev)), -1).cpu()
            P.append(pr.argmax(-1)); C.append(pr.max(-1).values); Y.append(y); R.append(pr)
    p, conf, y = torch.cat(P).numpy(), torch.cat(C).numpy(), torch.cat(Y).numpy()
    PROB = torch.cat(R).numpy()
    L = list(range(len(classes)))

    print(f"\n=== test (n={len(y):,}) · {backbone} ===")
    print(f"UAR {recall_score(y,p,labels=L,average='macro',zero_division=0):.4f}   "
          f"WAR {accuracy_score(y,p):.4f}   "
          f"macroF1 {f1_score(y,p,labels=L,average='macro',zero_division=0):.4f}")
    print(classification_report(y, p, labels=L, target_names=classes, digits=3, zero_division=0))
    cm = confusion_matrix(y, p, labels=L)
    print("혼동행렬 (행=정답, 행정규화 %)")
    print(pd.DataFrame((cm / np.maximum(cm.sum(1, keepdims=True), 1) * 100).round(1),
                       index=classes, columns=classes).to_string())

    sub = d_te.copy()
    sub["pred"] = [classes[i] for i in p]; sub["conf"] = conf
    sub["correct"] = (p == y).astype(float)
    for i, c in enumerate(classes):          # 앙상블용 클래스별 확률
        sub[f"prob_{c}"] = PROB[:, i]
    sub.to_csv(os.path.join(ckpt_dir, "eval_test.csv"), index=False, encoding="utf-8-sig")
    print("\n[임계값별 커버리지 / 정확도]")
    for th in (0.5, 0.6, 0.7, 0.8, 0.9):
        msk = sub.conf >= th
        if msk.sum():
            print(f"  >= {th:.1f} : 커버리지 {msk.mean():6.1%}  정확도 {sub.loc[msk,'correct'].mean():6.1%}")
    if writer:
        writer.add_scalar("test/UAR", recall_score(y, p, labels=L, average="macro", zero_division=0), 0)
        writer.add_scalar("test/WAR_accuracy", accuracy_score(y, p), 0)
        writer.close()
    print(f"\n[saved] {ckpt_dir}")
    print(f"최고 val UAR = {best:.4f}")


if __name__ == "__main__":
    main()
