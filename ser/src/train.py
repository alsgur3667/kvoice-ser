# -*- coding: utf-8 -*-
"""
6단계: 학습 (단일 GPU / DDP 2x4060 공용)

단일 GPU:
  python src/train.py --config configs/base.yaml
서버 2장:
  torchrun --nproc_per_node=2 src/train.py --config configs/base.yaml

4060 8GB 메모리 전략:
  bf16 + gradient checkpointing + batch 8 + grad_accum 4  ->  base 백본 약 6.5GB
  large 백본은 use_lora: true + batch 4 + max_sec 6.0 으로 낮출 것.
"""
import argparse, os, math, json, time
import numpy as np, pandas as pd, torch, yaml
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader
from sklearn.metrics import recall_score, f1_score, accuracy_score, confusion_matrix

sys_path = os.path.dirname(os.path.abspath(__file__))
import sys; sys.path.insert(0, sys_path)
from dataset import SERDataset, collate, balanced_sampler
from model import SERModel, param_groups
from losses import build_loss
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from wpath import wp
try:
    from torch.utils.tensorboard import SummaryWriter
    import tb as tbviz
    _TB = True
except Exception:                       # tensorboard 미설치여도 학습은 그대로 진행
    _TB = False


def is_main(): return not dist.is_initialized() or dist.get_rank() == 0


def evaluate(model, loader, dev, classes):
    model.eval(); P, Y = [], []
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
        for b in loader:
            lo = model(b["input_values"].to(dev), b["attention_mask"].to(dev))
            P.append(lo.float().argmax(-1).cpu()); Y.append(b["y"])
    p = torch.cat(P).numpy(); y = torch.cat(Y).numpy()
    return {
        "acc": accuracy_score(y, p),                              # WAR
        "uar": recall_score(y, p, average="macro", zero_division=0),  # 주 지표
        "f1": f1_score(y, p, average="macro", zero_division=0),
        "cm": confusion_matrix(y, p, labels=list(range(len(classes)))).tolist(),
    }


CKPT_DIR = None   # 크래시 로그를 어디에 쓸지 (__main__ 핸들러가 읽는다)


def main():
    global CKPT_DIR
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/base.yaml")
    ap.add_argument("--run", default=None)
    ap.add_argument("--init-from", default=None, metavar="CKPT",
                    help="기존 체크포인트에서 이어서 학습한다. "
                         "예: work/ckpt/pilot_1006/best.pt")
    ap.add_argument("--smoke", type=int, default=0, metavar="N",
                    help="N 배치만 돌려보고 끝낸다. 크래시 여부를 3시간이 아니라 "
                         "3분 만에 확인하는 용도. 체크포인트는 저장하지 않는다.")
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    T, work = cfg["train"], cfg["paths"]["work_root"]
    classes = cfg["label"]["classes"]

    ddp = int(os.environ.get("WORLD_SIZE", 1)) > 1
    if ddp:
        dist.init_process_group("nccl")
        local = int(os.environ["LOCAL_RANK"]); torch.cuda.set_device(local)
        dev = torch.device("cuda", local)
    else:
        dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    df = pd.read_csv(wp(cfg, "manifest_split.csv"))
    tr = SERDataset(df, cfg, "train", train=True)
    va = SERDataset(df, cfg, "val")

    if ddp:
        from torch.utils.data.distributed import DistributedSampler
        tr_sampler = DistributedSampler(tr, shuffle=True)
    else:
        tr_sampler = balanced_sampler(tr) if T["balanced_sampler"] else None

    dl_tr = DataLoader(tr, batch_size=T["batch_size"], sampler=tr_sampler,
                       shuffle=(tr_sampler is None), collate_fn=collate,
                       num_workers=T["num_workers"], pin_memory=True, drop_last=True,
                       persistent_workers=T["num_workers"] > 0)
    dl_va = DataLoader(va, batch_size=T["batch_size"] * 2, shuffle=False,
                       collate_fn=collate, num_workers=T["num_workers"])

    model = SERModel(cfg)

    # ---- 이어서 학습 ----
    # 백본 사전학습 가중치가 아니라 "우리가 이미 학습시킨 모델"에서 출발한다.
    # 도메인이 다른 데이터를 붙일 때 처음부터 다시 하지 않아도 되고,
    # 이미 배운 것을 유지한 채 새 데이터를 얹을 수 있다.
    if args.init_from:
        if not os.path.exists(args.init_from):
            raise SystemExit(f"[FAIL] 없는 체크포인트: {args.init_from}")
        ck0 = torch.load(args.init_from, map_location="cpu", weights_only=False)
        prev_cfg = ck0.get("cfg", {})
        prev_cls = prev_cfg.get("label", {}).get("classes")
        if prev_cls and list(prev_cls) != list(classes):
            raise SystemExit(
                "[FAIL] 클래스가 다릅니다. 헤드를 그대로 이어받을 수 없습니다.\n"
                f"  체크포인트: {prev_cls}\n  지금 설정   : {classes}")
        prev_bb = prev_cfg.get("model", {}).get("backbone")
        now_bb = cfg["model"]["backbone"]
        if prev_bb and prev_bb != now_bb:
            raise SystemExit(
                f"[FAIL] 백본이 다릅니다: {prev_bb} -> {now_bb}\n"
                "  구조가 달라 가중치를 옮길 수 없습니다. config 의 backbone 을 맞추세요.")
        r = model.load_state_dict(ck0["model"], strict=False)
        miss = [k for k in getattr(r, "missing_keys", [])]
        unex = [k for k in getattr(r, "unexpected_keys", [])]
        if is_main():
            m0 = ck0.get("metrics", {})
            print(f"\n[이어서 학습] {args.init_from}")
            print(f"  이전 epoch {ck0.get('epoch','?')} · "
                  f"UAR {m0.get('uar',float('nan')):.4f} WAR {m0.get('acc',float('nan')):.4f}")
            if miss: print(f"  [warn] 체크포인트에 없던 파라미터 {len(miss)}개는 새로 초기화됩니다: {miss[:5]}")
            if unex: print(f"  [warn] 지금 모델에 없는 파라미터 {len(unex)}개는 버립니다: {unex[:5]}")
            if not miss and not unex: print("  모든 가중치를 그대로 이어받았습니다.")
        del ck0

    model = model.to(dev)
    if T["grad_checkpointing"]:
        try: model.backbone.gradient_checkpointing_enable()
        except Exception: pass
    if ddp:
        model = DDP(model, device_ids=[dev.index], find_unused_parameters=True)

    counts = tr.df.label.map(tr.c2i).value_counts().reindex(range(len(classes)),
                                                            fill_value=1).sort_index().values
    hard_fn, soft_fn = build_loss(cfg, counts.astype(float))
    hard_fn = hard_fn.to(dev)
    sw = cfg["label"]["soft_weight"] if soft_fn else 0.0

    opt = torch.optim.AdamW(param_groups(model.module if ddp else model, cfg),
                            weight_decay=T["weight_decay"])
    steps = len(dl_tr) // T["grad_accum"] * T["epochs"]
    warm = int(steps * T["warmup_ratio"])
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: (
        s / max(1, warm) if s < warm else
        0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, steps - warm)))))

    run = args.run or time.strftime("%m%d_%H%M")
    ckpt_dir = os.path.join(work, "ckpt", run); os.makedirs(ckpt_dir, exist_ok=True)
    CKPT_DIR = ckpt_dir
    if is_main(): json.dump(cfg, open(f"{ckpt_dir}/config.json", "w"), ensure_ascii=False, indent=2)

    # --- TensorBoard ---  tensorboard --logdir work/tb
    writer = None
    if is_main() and _TB:
        tb_dir = os.path.join(work, "tb", run)
        writer = SummaryWriter(tb_dir)
        writer.add_text("config", "```\n" + yaml.safe_dump(cfg, allow_unicode=True) + "\n```")
        writer.add_text("run/데이터", f"train {len(tr):,} / val {len(va):,} · "
                                     f"화자 train {tr.df.spk.nunique()} / val {va.df.spk.nunique()}")
        print(f"[tensorboard] {tb_dir}\n  -> tensorboard --logdir {os.path.join(work,'tb')}")
    elif is_main():
        print("[tensorboard] 미설치 — pip install tensorboard 하면 다음 실행부터 기록됩니다")

    # ---- 백본 워밍업 동결 ----
    # 이어서 학습할 때 헤드는 이미 맞춰져 있지만 새 데이터의 분포는 다르다.
    # 처음 몇 epoch 백본을 얼려두면 큰 그래디언트가 백본을 흔드는 걸 막을 수 있다.
    # 원래 학습 대상이던 파라미터만 토글한다(freeze_feature_encoder 설정을 존중).
    _bb = (model.module if ddp else model).backbone
    _bb_trainable = [p for p in _bb.parameters() if p.requires_grad]
    freeze_eps = int(T.get("freeze_backbone_epochs", 0) or 0)
    if freeze_eps and is_main():
        print(f"[백본] 처음 {freeze_eps} epoch 은 동결하고 헤드만 학습합니다 "
              f"(대상 파라미터 {len(_bb_trainable)}개)")

    real_epochs = T["epochs"]
    if args.smoke:
        T["epochs"] = 1
        print(f"\n[SMOKE] {args.smoke} 배치만 돌립니다. 저장 안 함. "
              f"여기서 안 죽으면 본 학습도 안 죽습니다.\n")

    best, bad, gstep = -1, 0, 0
    val_every = int(T.get("val_every", 0) or 0)   # >0 이면 epoch 중간에도 검증/저장

    def mid_validate(ep, i, gs):
        """epoch 중간 검증. best 가 갱신되면 저장만 하고, early-stop 카운터는 건드리지 않는다.
        (epoch 단위 patience 의미를 흐리지 않기 위해서다.)
        TensorBoard 축이 epoch 단위인 val/* 과 섞이지 않도록 val_mid/* 로 따로 기록한다."""
        nonlocal best
        m = evaluate(model.module if ddp else model, dl_va, dev, classes)
        print(f"  [중간검증 ep{ep} {i}/{len(dl_tr)}] UAR {m['uar']:.4f}  "
              f"WAR {m['acc']:.4f}  F1 {m['f1']:.4f}", flush=True)
        if writer is not None:
            writer.add_scalar("val_mid/UAR", m["uar"], gs)
            writer.add_scalar("val_mid/macroF1", m["f1"], gs)
            writer.flush()
        if m[T["monitor"]] > best:
            best = m[T["monitor"]]
            torch.save({"model": (model.module if ddp else model).state_dict(),
                        "cfg": cfg, "metrics": m, "epoch": ep},
                       os.path.join(ckpt_dir, "best.pt"))
            print(f"  -> best {T['monitor']}={best:.4f} 저장", flush=True)

    for ep in range(T["epochs"]):
        if freeze_eps:
            frozen = ep < freeze_eps
            for p in _bb_trainable:
                p.requires_grad = not frozen
            if is_main() and ep in (0, freeze_eps):
                print(f"  [백본] {'동결' if frozen else '해제'} (epoch {ep})")
        model.train()
        if ddp: tr_sampler.set_epoch(ep)
        run_loss, t0 = 0.0, time.time()
        if torch.cuda.is_available(): torch.cuda.reset_peak_memory_stats()
        opt.zero_grad(set_to_none=True)
        for i, b in enumerate(dl_tr):
            with torch.autocast("cuda", dtype=torch.bfloat16):
                lo = model(b["input_values"].to(dev), b["attention_mask"].to(dev))
                loss = (1 - sw) * hard_fn(lo.float(), b["y"].to(dev))
                if soft_fn is not None:
                    loss = loss + sw * soft_fn(lo.float(), b["soft"].to(dev))
            (loss / T["grad_accum"]).backward()
            if (i + 1) % T["grad_accum"] == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step(); sched.step(); opt.zero_grad(set_to_none=True); gstep += 1
            run_loss += loss.item()
            if args.smoke and (i + 1) >= args.smoke:
                el = time.time() - t0
                print(f"\n[SMOKE PASS] {i+1} 배치 통과 · {el:.0f}s")
                if torch.cuda.is_available():
                    tot = torch.cuda.get_device_properties(0).total_memory / 2**30
                    print(f"  peak VRAM {torch.cuda.max_memory_allocated()/2**30:.2f}GB "
                          f"(reserved {torch.cuda.max_memory_reserved()/2**30:.2f}GB) / {tot:.1f}GB")
                per = el / (i + 1)
                ep_min = per * len(dl_tr) / 60
                print(f"  배치당 {per:.3f}s -> 1 epoch 약 {ep_min:.0f}분 "
                      f"(검증 제외) -> {real_epochs} epoch 약 {ep_min*real_epochs/60:.1f}시간")
                if writer is not None: writer.close()
                return
            if writer is not None and (i + 1) % 20 == 0:
                gs = ep * len(dl_tr) + i + 1
                writer.add_scalar("train/loss_step", loss.item(), gs)
                writer.add_scalar("train/lr_backbone", sched.get_last_lr()[0], gs)
                writer.add_scalar("train/lr_head", sched.get_last_lr()[-1], gs)
            if is_main() and (i + 1) % 100 == 0:
                vram = (f" vram {torch.cuda.max_memory_allocated()/2**30:.1f}G"
                        if torch.cuda.is_available() else "")
                print(f"ep{ep} {i+1}/{len(dl_tr)} loss {run_loss/(i+1):.4f} "
                      f"lr {sched.get_last_lr()[0]:.2e}{vram}", flush=True)
            # epoch 한 바퀴가 2시간이 넘는 설정에서는, 중간에 죽으면 아무것도 안 남는다.
            # val_every 를 켜두면 최소한 best.pt 하나는 확보된다.
            if is_main() and val_every and (i + 1) % val_every == 0 and (i + 1) < len(dl_tr):
                mid_validate(ep, i + 1, ep * len(dl_tr) + i + 1)
                model.train()

        if is_main():
            m = evaluate(model.module if ddp else model, dl_va, dev, classes)
            vram = torch.cuda.max_memory_allocated()/2**30 if torch.cuda.is_available() else 0.0
            print(f"\n[ep{ep}] {time.time()-t0:.0f}s  loss {run_loss/len(dl_tr):.4f} | "
                  f"UAR {m['uar']:.4f}  WAR {m['acc']:.4f}  F1 {m['f1']:.4f} | peak VRAM {vram:.1f}GB")
            if writer is not None:
                writer.add_scalar("train/loss_epoch", run_loss / len(dl_tr), ep)
                writer.add_scalar("val/UAR", m["uar"], ep)
                writer.add_scalar("val/WAR_accuracy", m["acc"], ep)
                writer.add_scalar("val/macroF1", m["f1"], ep)
                writer.add_scalar("time/epoch_sec", time.time() - t0, ep)
                writer.add_scalar("time/peak_vram_GB", vram, ep)
                try:
                    writer.add_image("val/confusion",
                                     tbviz.confusion_figure(m["cm"], classes,
                                         f"val confusion · epoch {ep}"), ep)
                except Exception as e:
                    print(f"[tb] 혼동행렬 기록 실패: {e}")
                lw = torch.softmax((model.module if ddp else model).layer_w.detach().cpu(), 0)
                for li, wv in enumerate(lw.tolist()):
                    writer.add_scalar(f"layer_weight/L{li:02d}", wv, ep)
                writer.flush()
            score = m[T["monitor"]]
            if score > best:
                best, bad = score, 0
                torch.save({"model": (model.module if ddp else model).state_dict(),
                            "cfg": cfg, "metrics": m, "epoch": ep},
                           os.path.join(ckpt_dir, "best.pt"))
                print(f"  -> best {T['monitor']}={best:.4f} 저장")
            else:
                bad += 1
                if bad >= T["early_stop_patience"]:
                    print("early stop"); break
        if ddp: dist.barrier()

    if writer is not None:
        writer.add_hparams(
            {"backbone": cfg["model"]["backbone"], "epochs": T["epochs"],
             "batch": T["batch_size"], "accum": T["grad_accum"],
             "lr_backbone": T["lr_backbone"], "lr_head": T["lr_head"],
             "loss": T["loss"], "max_sec": cfg["audio"]["max_sec"],
             "min_votes": cfg["label"]["min_votes"]},
            {f"best/{T['monitor']}": best})
        writer.close()
    if is_main():
        print(f"\n최고 {T['monitor']} = {best:.4f}  ({ckpt_dir}/best.pt)")
        print(f"학습 곡선 보기:  tensorboard --logdir {os.path.join(work, 'tb')}")
    if ddp: dist.destroy_process_group()


if __name__ == "__main__":
    # 크래시가 나도 이유를 남긴다.
    # xlsr_1705 는 37초 만에 죽었는데 콘솔이 닫혀서 원인을 못 봤다. 그 재발 방지.
    import traceback
    try:
        main()
    except Exception:
        tb = traceback.format_exc()
        print("\n" + "=" * 60)
        print(tb)
        print("=" * 60)
        if CKPT_DIR:
            p = os.path.join(CKPT_DIR, "error.log")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(tb)
                if torch.cuda.is_available():
                    fh.write("\n[vram] peak alloc %.2f GB / reserved %.2f GB / total %.2f GB\n" % (
                        torch.cuda.max_memory_allocated() / 2**30,
                        torch.cuda.max_memory_reserved() / 2**30,
                        torch.cuda.get_device_properties(0).total_memory / 2**30))
            print(f"[saved] {p}")
        if "CUDA out of memory" in tb:
            print("\n[진단] VRAM 부족입니다. config 에서 batch_size 를 절반으로,")
            print("       grad_accum 을 두 배로 올리세요 (실효 배치는 그대로 유지됩니다).")
            print("       그래도 나면 audio.max_sec 을 6.0 -> 5.0 으로 줄이세요.")
        raise SystemExit(1)
