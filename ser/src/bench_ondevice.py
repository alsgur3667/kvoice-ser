# -*- coding: utf-8 -*-
"""온디바이스 배포 가능성 측정.

발표에서 "온디바이스로 돌아갑니다"라고 말하려면 숫자가 있어야 한다.
이 스크립트가 재는 것:
  1) 모델 크기       fp32 / int8
  2) 추론 지연시간   발화 길이별 · 스레드 수별 (p50, p95)
  3) RTF             실시간 계수. 1.0 미만이어야 통화보다 빨리 처리한다
  4) 최대 메모리
  5) 양자화의 정확도 비용  <- 이게 핵심이다.
     작아지고 빨라진 건 당연하고, UAR 을 얼마나 잃었는지가 판단 기준이다.

주의: WavLM 의 어텐션은 q_proj.bias 를 속성으로 직접 참조하는데,
      동적 양자화를 하면 bias 가 메서드가 되어 forward 가 깨진다.
      그래서 어텐션 투영은 제외하고 FFN 쪽 Linear 만 int8 로 바꾼다.

  python src/bench_ondevice.py --ckpt work/ckpt/full_1731/best.pt
  python src/bench_ondevice.py --ckpt ... --no-eval      # 속도/크기만, 1분
"""
import argparse, os, sys, time, json, statistics, tempfile, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, torch
from torch.utils.data import DataLoader
from sklearn.metrics import recall_score, accuracy_score, f1_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wpath import wp
from dataset import SERDataset, collate
from model import SERModel


def peak_mem_mb():
    try:
        import resource
        r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return r / 1024 if sys.platform != "darwin" else r / 2**20   # 리눅스는 KB
    except Exception:
        return float("nan")


def quantize(model):
    """어텐션을 피해서 FFN Linear 만 int8 로."""
    names = {n for n, mod in model.named_modules()
             if isinstance(mod, torch.nn.Linear) and ".attention." not in n}
    q = torch.ao.quantization.quantize_dynamic(model, qconfig_spec=names,
                                               dtype=torch.qint8)
    return q.eval(), len(names)


def size_mb(model):
    p = tempfile.mktemp()
    torch.save(model.state_dict(), p)
    v = os.path.getsize(p) / 2**20
    os.remove(p)
    return v


def latency(model, sec, threads, n=15, warm=4):
    torch.set_num_threads(threads)
    x = torch.zeros(1, int(16000 * sec))
    mask = torch.ones(1, int(16000 * sec), dtype=torch.long)
    with torch.no_grad():
        for _ in range(warm):
            model(x, mask)
        ts = []
        for _ in range(n):
            t = time.perf_counter()
            model(x, mask)
            ts.append((time.perf_counter() - t) * 1000)
    ts.sort()
    return statistics.median(ts), ts[min(int(len(ts) * 0.95), len(ts) - 1)]


@torch.no_grad()
def score(model, dl, classes):
    P, Y = [], []
    for b in dl:
        lo = model(b["input_values"], b["attention_mask"]).float()
        P.append(lo.argmax(-1)); Y.append(b["y"])
    p, y = torch.cat(P).numpy(), torch.cat(Y).numpy()
    L = list(range(len(classes)))
    return dict(uar=recall_score(y, p, labels=L, average="macro", zero_division=0),
                war=accuracy_score(y, p),
                f1=f1_score(y, p, labels=L, average="macro", zero_division=0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--limit", type=int, default=600,
                    help="정확도 비교에 쓸 샘플 수. CPU 추론이라 전체는 오래 걸린다")
    ap.add_argument("--threads", default="1,2,4,8")
    ap.add_argument("--secs", default="1,3,5,10")
    ap.add_argument("--no-eval", action="store_true")
    ap.add_argument("--out", default="work/ondevice_bench.csv")
    a = ap.parse_args()

    ck = torch.load(a.ckpt, map_location="cpu", weights_only=False)
    cfg = ck["cfg"]; classes = cfg["label"]["classes"]
    model = SERModel(cfg); model.load_state_dict(ck["model"]); model.eval()

    print("=" * 72)
    print(f"  온디바이스 벤치마크   {a.ckpt}")
    print(f"  백본 {cfg['model']['backbone']}")
    try:
        import platform
        print(f"  CPU {os.cpu_count()}코어 · {platform.processor() or platform.machine()}")
    except Exception:
        pass
    print("=" * 72)

    tot = sum(p.numel() for p in model.parameters())
    print(f"\n[1] 모델 크기")
    print(f"  파라미터 {tot/1e6:.2f} M")
    s32 = size_mb(model)
    qmodel, nq = quantize(model)
    s8 = size_mb(qmodel)
    print(f"  fp32 {s32:7.1f} MB")
    print(f"  int8 {s8:7.1f} MB   ({(1-s8/s32)*100:.0f}% 감소 · Linear {nq}개 양자화)")

    secs = [float(x) for x in a.secs.split(",")]
    threads = [int(x) for x in a.threads.split(",") if int(x) <= (os.cpu_count() or 1)]

    print(f"\n[2] 추론 지연시간 (중앙값 / p95, 단위 ms)")
    rows = []
    for tag, mdl in (("fp32", model), ("int8", qmodel)):
        print(f"\n  {tag}")
        print("    " + f"{'threads':<9}" + "".join(f"{str(s)+'초':>16}" for s in secs))
        for th in threads:
            cells = []
            for s in secs:
                med, p95 = latency(mdl, s, th)
                cells.append(f"{med:.0f} / {p95:.0f}")
                rows.append(dict(precision=tag, threads=th, sec=s, p50_ms=med, p95_ms=p95,
                                 rtf=med / 1000 / s))
            print("    " + f"{th:<9}" + "".join(f"{c:>16}" for c in cells))

    df = pd.DataFrame(rows)
    best = df[(df.sec == 3)].sort_values("p50_ms").iloc[0]
    print(f"\n  가장 빠른 3초 처리: {best.precision} · {int(best.threads)}스레드 · "
          f"{best.p50_ms:.0f}ms · RTF {best.rtf:.3f}")
    print(f"  RTF {best.rtf:.3f} -> 1초 분량 통화를 {best.rtf*1000:.0f}ms 에 처리. "
          f"통화 1건을 실시간으로 따라가면서 CPU 의 {best.rtf*100:.0f}%만 쓴다.")

    if not a.no_eval:
        print(f"\n[3] 양자화의 정확도 비용  (작아진 대가로 무엇을 잃었나)")
        mani = a.manifest or wp(cfg, "manifest_split.csv")
        d = pd.read_csv(mani)
        ds = SERDataset(d, cfg, a.split)
        if a.limit and len(ds.df) > a.limit:
            ds.df = ds.df.sample(a.limit, random_state=42).reset_index(drop=True)
            print(f"  {a.split} 에서 {a.limit}개 표본 (전체 {len(d[d.split==a.split]) if 'split' in d else len(d):,}개)")
        dl = DataLoader(ds, batch_size=8, collate_fn=collate, num_workers=2)
        torch.set_num_threads(os.cpu_count() or 1)
        out = {}
        for tag, mdl in (("fp32", model), ("int8", qmodel)):
            t0 = time.time()
            out[tag] = score(mdl, dl, classes)
            print(f"  {tag} 완료 ({time.time()-t0:.0f}s)")
        print(f"\n  {'':<8}{'UAR':>10}{'WAR':>10}{'macroF1':>10}")
        for tag in ("fp32", "int8"):
            m = out[tag]
            print(f"  {tag:<8}{m['uar']:>10.4f}{m['war']:>10.4f}{m['f1']:>10.4f}")
        d_uar = out["int8"]["uar"] - out["fp32"]["uar"]
        print(f"  {'차이':<8}{d_uar:>+10.4f}{out['int8']['war']-out['fp32']['war']:>+10.4f}"
              f"{out['int8']['f1']-out['fp32']['f1']:>+10.4f}")
        print(f"\n  판정: 크기 {(1-s8/s32)*100:.0f}% 감소 · 속도 "
              f"{(1-df[(df.precision=='int8')&(df.sec==3)].p50_ms.min()/df[(df.precision=='fp32')&(df.sec==3)].p50_ms.min())*100:.0f}% 단축 "
              f"· UAR {d_uar:+.4f}")
        if d_uar > -0.01:
            print("  -> 손실이 0.01 미만이다. 양자화 모델을 배포해도 된다.")
        else:
            print("  -> 손실이 크다. fp16 이나 QAT(양자화 인지 학습)를 검토해야 한다.")
        for tag in out:
            rows.append(dict(precision=tag, threads=-1, sec=-1, **{f"acc_{k}": v for k, v in out[tag].items()}))
        df = pd.DataFrame(rows)

    print(f"\n[4] 최대 메모리 {peak_mem_mb():.0f} MB")
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    df.to_csv(a.out, index=False, encoding="utf-8-sig")
    print(f"\n[saved] {a.out}")


if __name__ == "__main__":
    main()
