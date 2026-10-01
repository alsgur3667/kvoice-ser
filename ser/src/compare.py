# -*- coding: utf-8 -*-
"""
백본 비교표 — work/ckpt 아래 모든 실험을 test 로 평가해 한 표로 묶는다.
  python src/compare.py                 # 전부
  python src/compare.py --runs a b c    # 지정한 것만
"""
import argparse, os, sys, glob, json
import numpy as np, pandas as pd, torch
from torch.utils.data import DataLoader
from sklearn.metrics import recall_score, f1_score, accuracy_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataset import SERDataset, collate
from model import SERModel


def eval_one(ckpt_path, dev):
    ck = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    cfg, classes = ck["cfg"], ck["cfg"]["label"]["classes"]
    df = pd.read_csv(os.path.join(cfg["paths"]["work_root"], "manifest_split.csv"))
    ds = SERDataset(df, cfg, "test")
    dl = DataLoader(ds, batch_size=16, shuffle=False, collate_fn=collate, num_workers=0)

    m = SERModel(cfg)
    if cfg["model"].get("use_lora"):
        from peft import LoraConfig, get_peft_model
        m.backbone = get_peft_model(m.backbone, LoraConfig(
            r=cfg["model"].get("lora_r", 16), lora_alpha=cfg["model"].get("lora_r", 16) * 2,
            lora_dropout=0.05, target_modules=["q_proj", "k_proj", "v_proj", "out_proj"],
            bias="none"))
    m.load_state_dict(ck["model"]); m.to(dev).eval()

    P, Y, C = [], [], []
    with torch.no_grad(), torch.autocast(dev.type, dtype=torch.bfloat16, enabled=dev.type == "cuda"):
        for b in dl:
            pr = torch.softmax(m(b["input_values"].to(dev),
                                 b["attention_mask"].to(dev)).float(), -1).cpu()
            P.append(pr.argmax(-1)); C.append(pr.max(-1).values); Y.append(b["y"])
    p, y, c = torch.cat(P).numpy(), torch.cat(Y).numpy(), torch.cat(C).numpy()
    L = list(range(len(classes)))
    correct = (p == y).astype(float)
    hi = c >= 0.70
    del m
    if dev.type == "cuda": torch.cuda.empty_cache()
    return {
        "backbone": cfg["model"]["backbone"].split("/")[-1],
        "lora": bool(cfg["model"].get("use_lora")),
        "min_votes": cfg["label"]["min_votes"],
        "epochs_run": ck.get("epoch", -1) + 1,
        "n_test": len(y),
        "UAR": recall_score(y, p, labels=L, average="macro", zero_division=0),
        "WAR": accuracy_score(y, p),
        "macroF1": f1_score(y, p, labels=L, average="macro", zero_division=0),
        "conf>=0.7_커버리지": hi.mean(),
        "conf>=0.7_정확도": correct[hi].mean() if hi.any() else np.nan,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="./work")
    ap.add_argument("--runs", nargs="*", default=None)
    args = ap.parse_args()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    paths = sorted(glob.glob(os.path.join(args.work, "ckpt", "*", "best.pt")))
    if args.runs:
        paths = [p for p in paths if os.path.basename(os.path.dirname(p)) in args.runs]
    if not paths:
        sys.exit(f"{args.work}/ckpt 아래에 best.pt 가 없습니다.")

    rows = []
    for p in paths:
        run = os.path.basename(os.path.dirname(p))
        print(f"[eval] {run} ...", flush=True)
        try:
            r = eval_one(p, dev); r["run"] = run; rows.append(r)
        except Exception as e:
            print(f"  건너뜀: {str(e)[:120]}")

    if not rows: sys.exit("평가된 실험이 없습니다.")
    df = pd.DataFrame(rows)[["run", "backbone", "lora", "min_votes", "epochs_run", "n_test",
                             "UAR", "WAR", "macroF1", "conf>=0.7_커버리지", "conf>=0.7_정확도"]]
    df = df.sort_values("UAR", ascending=False)
    pd.set_option("display.width", 200)
    print("\n" + "=" * 100)
    print(df.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print("=" * 100)
    print(f"\n7클래스 랜덤 UAR = {1/7:.3f}")
    out = os.path.join(args.work, "backbone_comparison.csv")
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"[saved] {out}")


if __name__ == "__main__":
    main()
