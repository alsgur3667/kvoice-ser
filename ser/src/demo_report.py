# -*- coding: utf-8 -*-
"""
긴 오디오 -> 감정 타임라인 리포트 (발표 데모용)

한 발화만 분류하는 게 아니라, 통화 전체를 창으로 훑어서
'언제 감정이 바뀌었는지'를 그림 한 장으로 만든다.

  python src/demo_report.py --ckpt work/ckpt/pilot_1006/best.pt --wav demo/demo_long_3.wav
"""
import argparse, os, sys, json
import warnings
import numpy as np, pandas as pd, torch, librosa
warnings.filterwarnings('ignore')
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import SERModel

KO = {"angry": "분노", "sadness": "슬픔", "happy": "기쁨", "neutral": "중립",
      "fear": "두려움", "disgust": "혐오", "surprise": "놀람"}
# 운영 액션 = 고정 상태색 (시리즈 색으로 재사용 금지)
STATUS = {"angry": ("critical", "#d03b3b", "에스컬레이션"),
          "disgust": ("critical", "#d03b3b", "에스컬레이션"),
          "sadness": ("serious", "#ec835a", "케어"),
          "fear": ("serious", "#ec835a", "케어"),
          "surprise": ("warning", "#fab219", "관찰"),
          "happy": ("good", "#0ca30c", "정상"),
          "neutral": ("good", "#0ca30c", "정상")}
VALENCE = {"angry": -.80, "disgust": -.70, "fear": -.65, "sadness": -.75,
           "neutral": 0.0, "happy": .85, "surprise": .10}
AROUSAL = {"angry": .85, "disgust": .40, "fear": .70, "sadness": -.55,
           "neutral": -.30, "happy": .50, "surprise": .80}


def set_font():
    avail = {f.name for f in font_manager.fontManager.ttflist}
    for f in ("Malgun Gothic", "AppleGothic", "NanumGothic"):
        if f in avail:
            matplotlib.rcParams["font.family"] = f; return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--wav", required=True)
    ap.add_argument("--win", type=float, default=3.0)
    ap.add_argument("--hop", type=float, default=1.0)
    ap.add_argument("--th", type=float, default=0.70, help="신뢰도 임계값")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    ko = set_font()
    if not ko: print("[warn] 한글 폰트 없음 - 그래프 한글이 깨질 수 있습니다")

    ck = torch.load(args.ckpt, map_location="cpu", weights_only=False)
    cfg, classes = ck["cfg"], ck["cfg"]["label"]["classes"]
    sr = cfg["audio"]["sample_rate"]
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    m = SERModel(cfg)
    if cfg["model"].get("use_lora"):
        from peft import LoraConfig, get_peft_model
        r = cfg["model"].get("lora_r", 16)
        m.backbone = get_peft_model(m.backbone, LoraConfig(
            r=r, lora_alpha=r * 2, lora_dropout=0.05,
            target_modules=["q_proj", "k_proj", "v_proj", "out_proj"], bias="none"))
    m.load_state_dict(ck["model"]); m.to(dev).eval()
    print(f"[model] {cfg['model']['backbone']}  (val {ck['metrics']['uar']:.4f} @ ep{ck['epoch']})")

    y = librosa.load(args.wav, sr=sr, mono=True)[0]
    y = y - y.mean()
    pk = np.abs(y).max()
    if pk > 1e-5: y = y / pk * 0.891
    total = len(y) / sr
    print(f"[audio] {os.path.basename(args.wav)} · {total:.1f}초 · {sr}Hz")

    W, H = int(args.win * sr), int(args.hop * sr)
    rows = []
    with torch.no_grad(), torch.autocast(dev.type, dtype=torch.bfloat16, enabled=dev.type == "cuda"):
        for s in range(0, max(1, len(y) - W + 1), H):
            seg = y[s:s + W]
            if len(seg) < sr * 0.8: break
            if np.abs(seg).max() < 0.02:          # 무음 창은 건너뛴다
                rows.append({"t": s / sr, "label": None}); continue
            pr = torch.softmax(m(torch.from_numpy(seg)[None].to(dev)).float(), -1)[0].cpu().numpy()
            p = dict(zip(classes, pr.astype(float)))
            top = classes[int(pr.argmax())]
            rows.append({"t": round(s / sr, 2), "label": top, "label_ko": KO.get(top, top),
                         "conf": float(pr.max()),
                         "valence": round(sum(p[k] * VALENCE[k] for k in classes), 3),
                         "arousal": round(sum(p[k] * AROUSAL[k] for k in classes), 3),
                         "neg": round(p.get("angry", 0) + p.get("disgust", 0), 4),
                         **{f"p_{k}": round(v, 4) for k, v in p.items()}})

    df = pd.DataFrame([r for r in rows if r.get("label")])
    n_sil = len(rows) - len(df)
    if df.empty: sys.exit("분석 가능한 구간이 없습니다.")

    rel = df[df.conf >= args.th]
    neg_ratio = (rel.label.isin(["angry", "disgust"]).mean() if len(rel) else 0.0)
    print(f"[분석] 창 {args.win}s / 홉 {args.hop}s · 구간 {len(df)}개 (무음 {n_sil}개 제외)")
    print(f"       신뢰 구간(>= {args.th}) {len(rel)}개 = {len(rel)/len(df):.0%}")
    print(f"\n[감정 분포]  (신뢰 구간 기준)")
    if len(rel):
        for k, v in rel.label_ko.value_counts().items():
            print(f"  {k:5s} {v:3d}구간 ({v/len(rel):5.1%})")
    print(f"\n[부정 감정(분노+혐오) 비율] {neg_ratio:.1%}"
          f"  -> {'에스컬레이션 권고' if neg_ratio > 0.30 else '정상 범위'}")
    pk_row = df.loc[df.neg.idxmax()]
    print(f"[최고조] {pk_row.t:.1f}초 · {pk_row.label_ko} · 부정확률 {pk_row.neg:.1%}")

    # ---------------- 그림 ----------------
    fig, ax = plt.subplots(3, 1, figsize=(13, 7.4),
                           gridspec_kw={"height_ratios": [1.0, 0.34, 1.5], "hspace": 0.28},
                           sharex=True)

    t = np.arange(len(y)) / sr
    ax[0].plot(t, y, lw=.3, color="#86b6ef")
    ax[0].set_ylabel("파형"); ax[0].set_xlim(0, total)
    ax[0].set_title(f"{os.path.basename(args.wav)}   ·   {total:.0f}초   ·   "
                    f"부정 감정 구간 {neg_ratio:.0%}  (신뢰도 {args.th} 이상 기준)",
                    fontsize=12, loc="left")
    ax[0].grid(alpha=.2)

    for _, r in df.iterrows():
        c = STATUS.get(r.label, ("good", "#0ca30c", ""))[1]
        a = 1.0 if r.conf >= args.th else 0.28          # 저신뢰는 흐리게
        ax[1].add_patch(plt.Rectangle((r.t, 0), args.hop * 0.92, 1,
                                      color=c, alpha=a, linewidth=0))
    ax[1].set_ylim(0, 1); ax[1].set_yticks([]); ax[1].set_ylabel("감정", rotation=0,
                                                                 ha="right", va="center")

    ax[2].fill_between(df.t, df.neg, color="#d03b3b", alpha=.16)
    ax[2].plot(df.t, df.neg, color="#d03b3b", lw=2, label="부정 (분노+혐오)")
    ax[2].plot(df.t, df.valence, color="#2a78d6", lw=1.6, ls="-", label="Valence (긍/부정)")
    ax[2].plot(df.t, df.arousal, color="#1baf7a", lw=1.6, ls="--", label="Arousal (각성도)")
    ax[2].axhline(0, color="#c3c2b7", lw=1)
    ax[2].axvline(pk_row.t, color="#d03b3b", lw=1, ls=":", alpha=.7)
    ax[2].annotate(f"최고조 {pk_row.t:.0f}s", (pk_row.t, 1.0), fontsize=9,
                   color="#d03b3b", ha="center", va="bottom")
    ax[2].set_ylim(-1.05, 1.05); ax[2].set_xlabel("시간 (초)"); ax[2].set_ylabel("점수")
    ax[2].legend(fontsize=9, ncol=3, loc="lower right"); ax[2].grid(alpha=.25)

    handles = [plt.Rectangle((0, 0), 1, 1, color=v[1]) for v in
               [("", "#d03b3b", ""), ("", "#ec835a", ""), ("", "#fab219", ""), ("", "#0ca30c", "")]]
    ax[1].legend(handles, ["에스컬레이션 · 분노/혐오", "케어 · 슬픔/두려움",
                           "관찰 · 놀람", "정상 · 기쁨/중립"],
                 fontsize=8.5, ncol=4, loc="lower center", bbox_to_anchor=(.5, 1.05),
                 frameon=False, handlelength=1.2, columnspacing=1.6)
    ax[1].text(0.005, -0.42, "흐린 색 = 신뢰도 미달", transform=ax[1].transAxes,
               fontsize=8, color="#898781")

    out = args.out or os.path.splitext(args.wav)[0] + "_timeline.png"
    fig.subplots_adjust(left=0.07, right=0.985, top=0.93, bottom=0.08)
    fig.savefig(out, dpi=140, facecolor="white"); plt.close(fig)
    csv = os.path.splitext(out)[0] + ".csv"
    df.to_csv(csv, index=False, encoding="utf-8-sig")
    print(f"\n[saved] {out}")
    print(f"[saved] {csv}")


if __name__ == "__main__":
    main()
