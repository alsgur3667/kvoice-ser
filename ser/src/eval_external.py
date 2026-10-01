# -*- coding: utf-8 -*-
"""
외부 데이터 교차 검증 — 학습에 전혀 안 쓴 다른 표본으로 평가한다.

라벨은 두 가지 방식으로 읽는다.
  --csv segments.csv     (emotion, path 컬럼)
  --from-filename        (seg02_ang.wav 처럼 마지막 _ 뒤 접미사)

  python src/eval_external.py --ckpt work/ckpt/pilot_1006/best.pt ^
      --dir "C:/Users/user/Desktop/검증voice" --csv segments.csv
"""
import argparse, os, sys, glob
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, torch, librosa
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from sklearn.metrics import (recall_score, accuracy_score, f1_score,
                             confusion_matrix, classification_report)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import SERModel

# 외부 데이터에서 흔히 쓰는 축약형 -> 우리 7클래스
ALIAS = {
    "neu": "neutral", "neutral": "neutral",
    "ang": "angry", "anger": "angry", "angry": "angry",
    "sad": "sadness", "sadness": "sadness",
    "hap": "happy", "happy": "happy", "happiness": "happy", "joy": "happy",
    "fea": "fear", "fear": "fear", "fearful": "fear",
    "dis": "disgust", "disgust": "disgust", "disgusted": "disgust",
    "sur": "surprise", "surprise": "surprise", "surprised": "surprise",
}
KO = {"angry": "분노", "sadness": "슬픔", "happy": "기쁨", "neutral": "중립",
      "fear": "두려움", "disgust": "혐오", "surprise": "놀람"}


def set_font():
    av = {f.name for f in font_manager.fontManager.ttflist}
    for f in ("Malgun Gothic", "AppleGothic", "NanumGothic"):
        if f in av: matplotlib.rcParams["font.family"] = f; return True
    return False


def load_model(ckpt, dev):
    ck = torch.load(ckpt, map_location="cpu", weights_only=False)
    cfg = ck["cfg"]
    m = SERModel(cfg)
    if cfg["model"].get("use_lora"):
        from peft import LoraConfig, get_peft_model
        r = cfg["model"].get("lora_r", 16)
        m.backbone = get_peft_model(m.backbone, LoraConfig(
            r=r, lora_alpha=r * 2, lora_dropout=0.05,
            target_modules=["q_proj", "k_proj", "v_proj", "out_proj"], bias="none"))
    m.load_state_dict(ck["model"]); m.to(dev).eval()
    return m, cfg, ck


@torch.no_grad()
def predict_probs(m, cfg, path, dev, chunk=True):
    """max_sec 보다 길면 창을 나눠 확률을 평균한다 (중앙 crop 보다 공정)."""
    sr = cfg["audio"]["sample_rate"]
    y = librosa.load(path, sr=sr, mono=True)[0]
    y = y - y.mean()
    pk = np.abs(y).max()
    if pk > 1e-5: y = y / pk * 0.891
    L = int(cfg["audio"]["max_sec"] * sr)
    segs = [y]
    if chunk and len(y) > L:
        hop = L // 2
        segs = [y[s:s + L] for s in range(0, len(y) - L + 1, hop)]
        if (len(y) - L) % hop: segs.append(y[-L:])
    out = []
    for s in segs:
        x = torch.from_numpy(s.astype(np.float32))[None].to(dev)
        with torch.autocast(dev.type, dtype=torch.bfloat16, enabled=dev.type == "cuda"):
            out.append(torch.softmax(m(x).float(), -1)[0].cpu().numpy())
    return np.mean(out, 0), len(segs), len(y) / sr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--ckpt2", default=None, help="두 번째 SERModel 체크포인트 (앙상블)")
    ap.add_argument("--e2v-head", default=None, help="emotion2vec 헤드 (head.pt)")
    ap.add_argument("--e2v-feats", default=None, help="이 폴더용 emotion2vec 특징 npz")
    ap.add_argument("--w", type=float, default=0.7, help="ckpt 가중치 (ckpt2 = 1-w)")
    ap.add_argument("--dir", default=None, help="생략하면 바탕화면에서 자동 탐색")
    ap.add_argument("--csv", default=None, help="라벨 CSV (emotion, path 컬럼)")
    ap.add_argument("--from-filename", action="store_true")
    ap.add_argument("--no-chunk", action="store_true")
    ap.add_argument("--th", type=float, default=0.70)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    ko = set_font()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    root = args.dir
    if not root:                      # 배치 파일에 한글 경로를 넣으면 cmd 가 깨지므로 여기서 찾는다
        home = os.path.expanduser("~")
        cands = [os.path.join(home, "Desktop", "검증voice"),
                 os.path.join(home, "OneDrive", "Desktop", "검증voice"),
                 os.path.join(home, "바탕 화면", "검증voice")]
        # 바탕화면 아래에서 segments.csv 를 가진 폴더도 훑는다
        for d in (os.path.join(home, "Desktop"), os.path.join(home, "OneDrive", "Desktop")):
            if os.path.isdir(d):
                for n in os.listdir(d):
                    q = os.path.join(d, n)
                    if os.path.isdir(q) and os.path.exists(os.path.join(q, "segments.csv")):
                        cands.append(q)
        root = next((c for c in cands if os.path.isdir(c)), None)
        if not root:
            sys.exit("검증 폴더를 못 찾았습니다. --dir 로 직접 지정하세요.")
        print(f"[auto] 검증 폴더: {root}")
    if not os.path.isdir(root):
        sys.exit(f"폴더가 없습니다: {root}")

    # ---- 라벨 수집 ----
    rows = []
    if args.csv:
        cp = args.csv if os.path.isabs(args.csv) else os.path.join(root, args.csv)
        for enc in ("utf-8-sig", "cp949", "utf-8"):
            try: meta = pd.read_csv(cp, encoding=enc); break
            except (UnicodeDecodeError, UnicodeError): continue
        cols = {c.lower(): c for c in meta.columns}
        ec = cols.get("emotion") or cols.get("label")
        pc = cols.get("path") or cols.get("file") or cols.get("filename")
        if not ec or not pc: sys.exit(f"CSV 에 emotion/path 컬럼이 필요합니다: {list(meta.columns)}")
        for r in meta.itertuples():
            lab = ALIAS.get(str(getattr(r, ec)).strip().lower())
            p = os.path.join(root, str(getattr(r, pc)))
            if lab and os.path.exists(p):
                rows.append({"path": p, "true": lab,
                             "text": str(getattr(r, cols["text"])) if "text" in cols else ""})
    else:
        for p in sorted(glob.glob(os.path.join(root, "*.wav"))):
            suf = os.path.splitext(os.path.basename(p))[0].split("_")[-1].lower()
            lab = ALIAS.get(suf)
            if lab: rows.append({"path": p, "true": lab, "text": ""})
    if not rows: sys.exit("라벨이 붙은 파일을 못 찾았습니다.")

    # ---- 모델 ----
    m1, cfg, ck1 = load_model(args.ckpt, dev)
    classes = cfg["label"]["classes"]
    print(f"[model] {cfg['model']['backbone']}  (val UAR {ck1['metrics']['uar']:.4f})")
    # emotion2vec 헤드 (선택)
    e2v = None
    if args.e2v_head:
        if not args.e2v_feats: sys.exit("--e2v-head 를 쓰려면 --e2v-feats 도 필요합니다.")
        from e2v_train import Head
        hk = torch.load(args.e2v_head, map_location="cpu", weights_only=False)
        if hk["classes"] != classes: sys.exit("클래스 순서가 다릅니다.")
        head = Head(hk["d_in"], len(classes)); head.load_state_dict(hk["head"])
        head.to(dev).eval()
        z = np.load(args.e2v_feats, allow_pickle=True)
        fmap = dict(zip([str(w) for w in z["wav_id"].tolist()], z["feats"]))
        e2v = (head, hk["mu"].to(dev), hk["sd"].to(dev), fmap)
        print(f"[model2] {hk['backbone']} 프리즈 + 헤드  ·  특징 {len(fmap)}개"
              f"  · 가중치 {args.w:.2f}/{1-args.w:.2f}")

    m2 = None
    if args.ckpt2:
        m2, cfg2, ck2 = load_model(args.ckpt2, dev)
        print(f"[model2] {cfg2['model']['backbone']}  (val UAR {ck2['metrics']['uar']:.4f})"
              f"  · 가중치 {args.w:.2f}/{1-args.w:.2f}")
    print(f"[data]  {root}  ·  {len(rows)}개\n")

    c2i = {c: i for i, c in enumerate(classes)}
    for r in rows:
        p1, n, dur = predict_probs(m1, cfg, r["path"], dev, not args.no_chunk)
        pr = p1
        if m2 is not None:
            p2, _, _ = predict_probs(m2, cfg2, r["path"], dev, not args.no_chunk)
            pr = args.w * p1 + (1 - args.w) * p2
        elif e2v is not None:
            head, mu, sd, fmap = e2v
            key = os.path.splitext(os.path.basename(r["path"]))[0]
            if key not in fmap:
                print(f"  [warn] {key}: emotion2vec 특징 없음 -> WavLM 단독 사용")
            else:
                x = torch.tensor(fmap[key], dtype=torch.float32)[None].to(dev)
                with torch.no_grad():
                    p2 = torch.softmax(head((x - mu) / sd), -1)[0].cpu().numpy()
                pr = args.w * p1 + (1 - args.w) * p2
                r["p_wavlm"] = classes[int(p1.argmax())]
                r["p_e2v"] = classes[int(p2.argmax())]
        r["pred"] = classes[int(pr.argmax())]
        r["conf"] = float(pr.max())
        r["dur"] = round(dur, 2); r["n_win"] = n
        r["ok"] = r["pred"] == r["true"]
        for i, c in enumerate(classes): r[f"prob_{c}"] = float(pr[i])

    df = pd.DataFrame(rows)
    y = df.true.map(c2i).values
    p = df.pred.map(c2i).values
    L = list(range(len(classes)))

    print("=" * 78)
    print(f"{'파일':<18}{'정답':<8}{'예측':<8}{'신뢰도':>8}  {'':2}  상위 3개 확률")
    print("-" * 78)
    for r in rows:
        top = sorted(((c, r[f"prob_{c}"]) for c in classes), key=lambda t: -t[1])[:3]
        ts = "  ".join(f"{KO.get(c,c)} {v*100:.0f}%" for c, v in top)
        print(f"{os.path.basename(r['path']):<18}{KO[r['true']]:<8}{KO[r['pred']]:<8}"
              f"{r['conf']*100:7.1f}%  {'O' if r['ok'] else 'X':2}  {ts}")
    print("=" * 78)

    acc = accuracy_score(y, p)
    uar = recall_score(y, p, labels=L, average="macro", zero_division=0)
    f1 = f1_score(y, p, labels=L, average="macro", zero_division=0)
    present = sorted(set(df.true))
    uar_p = recall_score(y, p, labels=[c2i[c] for c in present], average="macro", zero_division=0)
    print(f"\n정확도 {acc:.3f} ({df.ok.sum()}/{len(df)})   "
          f"UAR(7클래스) {uar:.3f}   UAR(등장 {len(present)}클래스) {uar_p:.3f}   F1 {f1:.3f}")
    print(f"신뢰도 >= {args.th}: {(df.conf>=args.th).sum()}/{len(df)}개, "
          f"그중 정답 {df[df.conf>=args.th].ok.sum() if (df.conf>=args.th).any() else 0}개")
    print(f"\n※ n={len(df)} 은 매우 작습니다. 한 개 차이가 {1/len(df)*100:.0f}%p 입니다.")

    print("\n" + classification_report(y, p, labels=[c2i[c] for c in present],
                                       target_names=present, digits=3, zero_division=0))

    # ---- 운영 액션 단위 평가 ----
    # 7클래스를 정확히 맞히는 것과, 서비스가 올바른 행동을 하는 것은 다르다.
    # 중립을 기쁨으로 착각해도 둘 다 '정상'이면 서비스는 같은 동작을 한다.
    GROUP = {"angry": "에스컬레이션", "disgust": "에스컬레이션",
             "sadness": "케어", "fear": "케어",
             "surprise": "관찰", "happy": "정상", "neutral": "정상"}
    df["true_g"] = df.true.map(GROUP); df["pred_g"] = df.pred.map(GROUP)
    gok = (df.true_g == df.pred_g)
    print(f"[운영 액션 단위] 정확도 {gok.mean():.3f} ({gok.sum()}/{len(df)})")
    for g in ["에스컬레이션", "케어", "관찰", "정상"]:
        m = df.true_g == g
        if m.sum():
            print(f"  {g:7s} {gok[m].sum()}/{m.sum()}")

    # ---- 극성 단위 (부정 / 중립·긍정) ----
    POL = {"angry": "부정", "disgust": "부정", "sadness": "부정", "fear": "부정",
           "surprise": "중립긍정", "happy": "중립긍정", "neutral": "중립긍정"}
    pok = (df.true.map(POL) == df.pred.map(POL))
    print(f"[극성 단위]      정확도 {pok.mean():.3f} ({pok.sum()}/{len(df)})")

    df["group_ok"] = gok.astype(int); df["pol_ok"] = pok.astype(int)

    # ---- 그림 ----
    fig, ax = plt.subplots(1, 2, figsize=(14, max(3.2, 0.42 * len(df))),
                           gridspec_kw={"width_ratios": [1.45, 1]})
    yy = np.arange(len(df))[::-1]
    ax[0].barh(yy, df.conf, color=["#1baf7a" if o else "#d03b3b" for o in df.ok], height=.62)
    ax[0].axvline(args.th, color="#898781", ls="--", lw=1)
    ax[0].set_yticks(yy)
    ax[0].set_yticklabels([f"{os.path.basename(r['path'])[:14]}  {KO[r['true']]}→{KO[r['pred']]}"
                           for r in rows], fontsize=8.5)
    ax[0].set_xlim(0, 1); ax[0].set_xlabel("신뢰도")
    ax[0].set_title(f"예측별 신뢰도  ·  정확도 {acc:.0%} ({df.ok.sum()}/{len(df)})", fontsize=11)
    ax[0].grid(axis="x", alpha=.25); ax[0].set_axisbelow(True)
    ax[0].text(args.th + .01, yy[0] + .6, f"임계값 {args.th}", fontsize=8, color="#898781")

    cm = confusion_matrix(y, p, labels=L)
    ax[1].imshow(cm, cmap="Blues", vmin=0)
    ax[1].set_xticks(L); ax[1].set_xticklabels([KO[c] for c in classes], rotation=45, ha="right",
                                               fontsize=8)
    ax[1].set_yticks(L); ax[1].set_yticklabels([KO[c] for c in classes], fontsize=8)
    ax[1].set_xlabel("예측"); ax[1].set_ylabel("정답"); ax[1].set_title("혼동행렬 (개수)", fontsize=11)
    for i in L:
        for j in L:
            if cm[i, j]:
                ax[1].text(j, i, cm[i, j], ha="center", va="center", fontsize=9,
                           color="white" if cm[i, j] > cm.max() * .6 else "black")
    out = args.out or os.path.join(root, "external_eval.png")
    fig.subplots_adjust(left=0.22, right=0.98, top=0.9, bottom=0.14, wspace=0.35)
    fig.savefig(out, dpi=140, facecolor="white"); plt.close(fig)
    csv_out = os.path.splitext(out)[0] + ".csv"
    df.drop(columns=["ok"]).assign(correct=df.ok.astype(int)).to_csv(
        csv_out, index=False, encoding="utf-8-sig")
    print(f"[saved] {out}")
    print(f"[saved] {csv_out}")


if __name__ == "__main__":
    main()
