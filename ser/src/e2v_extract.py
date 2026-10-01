# -*- coding: utf-8 -*-
"""
emotion2vec 특징 추출 (1단계)

emotion2vec 은 transformers 가 아니라 FunASR 프레임워크로 돌아간다.
기존 환경을 깨지 않으려고 별도 venv(.venv_e2v)에서 이 스크립트만 실행하고,
결과는 .npz 한 덩어리로 떨궈서 2단계(헤드 학습)는 원래 환경에서 돌린다.

가중치는 HuggingFace 에서 받아 로컬 경로로 넘긴다 (중국 서버 경유 없음).

  python src/e2v_extract.py --config configs/pilot.yaml
  python src/e2v_extract.py --model emotion2vec/emotion2vec_base   # SSL 원본
"""
import argparse, os, sys, time
import numpy as np, pandas as pd, yaml

# emotion2vec+ 의 9클래스 -> 우리 7클래스
E2V_MAP = {
    "angry": "angry", "생气/angry": "angry",
    "disgusted": "disgust", "fearful": "fear", "happy": "happy",
    "neutral": "neutral", "sad": "sadness", "surprised": "surprise",
    "other": None, "unknown": None,
}


def norm_label(s):
    """'生气/angry' 같은 중영 혼합 라벨에서 영문만 뽑는다."""
    s = str(s).strip().lower()
    if "/" in s:
        s = s.split("/")[-1].strip()
    return E2V_MAP.get(s, None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/pilot.yaml")
    ap.add_argument("--model", default="emotion2vec/emotion2vec_plus_large",
                    help="HF repo id. SSL 원본은 emotion2vec/emotion2vec_base")
    ap.add_argument("--out", default=None)
    ap.add_argument("--limit", type=int, default=0, help="테스트용으로 N개만")
    ap.add_argument("--dir", default=None,
                    help="manifest 대신 이 폴더의 wav 전부를 추출 (외부 데이터 검증용)")
    ap.add_argument("--dir-auto", action="store_true",
                    help="바탕화면에서 segments.csv 가 있는 폴더를 자동 탐색 "
                         "(배치 파일에 한글 경로를 넣으면 cmd 가 깨지므로)")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    work = cfg["paths"]["work_root"]

    if args.dir_auto and not args.dir:
        home = os.path.expanduser("~")
        cands = [os.path.join(home, "Desktop", "검증voice"),
                 os.path.join(home, "OneDrive", "Desktop", "검증voice")]
        for d in (os.path.join(home, "Desktop"), os.path.join(home, "OneDrive", "Desktop")):
            if os.path.isdir(d):
                for n in os.listdir(d):
                    q = os.path.join(d, n)
                    if os.path.isdir(q) and os.path.exists(os.path.join(q, "segments.csv")):
                        cands.append(q)
        args.dir = next((c for c in cands if os.path.isdir(c)), None)
        if not args.dir: sys.exit("검증 폴더를 못 찾았습니다. --dir 로 지정하세요.")
        print(f"[auto] 검증 폴더: {args.dir}")

    split_csv = os.path.join(work, "manifest_split.csv")
    if args.dir is None and not os.path.exists(split_csv):
        sys.exit(f"{split_csv} 가 없습니다. 먼저 train.bat 으로 split 까지 만드세요.")

    # ---- 1) 가중치를 HF 에서 로컬로 ----
    local_dir = os.path.join(work, "models", args.model.split("/")[-1])
    if not os.path.exists(os.path.join(local_dir, "model.pt")) and \
       not os.path.exists(os.path.join(local_dir, "emotion2vec_plus_large.pt")):
        print(f"[download] {args.model} -> {local_dir}")
        try:
            from huggingface_hub import snapshot_download
            snapshot_download(repo_id=args.model, local_dir=local_dir)
        except Exception as e:
            sys.exit(f"HF 다운로드 실패: {e}\n"
                     f"  huggingface-cli download {args.model} --local-dir \"{local_dir}\"\n"
                     f"  를 직접 실행한 뒤 다시 시도하세요.")
    else:
        print(f"[cache] {local_dir}")

    # ---- 2) FunASR 로드 ----
    try:
        from funasr import AutoModel
    except ImportError:
        sys.exit("funasr 가 없습니다.  pip install funasr  (별도 venv 권장)")

    print("[load] FunASR AutoModel ...")
    try:
        model = AutoModel(model=local_dir, disable_update=True)
    except Exception as e:
        print(f"  로컬 로드 실패({str(e)[:100]}) -> ModelScope 로 재시도")
        ms = "iic/" + args.model.split("/")[-1]
        model = AutoModel(model=ms, disable_update=True)

    # ---- 3) 추출 ----
    if args.dir:
        import glob
        files = sorted(glob.glob(os.path.join(args.dir, "*.wav")))
        if not files: sys.exit(f"{args.dir} 에 wav 가 없습니다.")
        df = pd.DataFrame({"wav_id": [os.path.splitext(os.path.basename(f))[0] for f in files],
                           "cache_path": files})
        print(f"[dir] {args.dir} · wav {len(df)}개")
    else:
        df = pd.read_csv(split_csv)
    if args.limit: df = df.head(args.limit)
    print(f"[extract] {len(df):,}개 · utterance 임베딩 + 제로샷 예측")

    ids, feats, zs_lab, zs_conf, failed = [], [], [], [], 0
    t0 = time.time()
    for i, r in enumerate(df.itertuples()):
        try:
            res = model.generate(r.cache_path, granularity="utterance",
                                 extract_embedding=True, disable_pbar=True)
            rec = res[0]
            emb = np.asarray(rec["feats"], dtype=np.float32).reshape(-1)
            ids.append(str(r.wav_id)); feats.append(emb)
            # 제로샷 분류 결과(있으면)
            if "labels" in rec and "scores" in rec:
                k = int(np.argmax(rec["scores"]))
                zs_lab.append(norm_label(rec["labels"][k]))
                zs_conf.append(float(rec["scores"][k]))
            else:
                zs_lab.append(None); zs_conf.append(np.nan)
        except Exception as e:
            failed += 1
            if failed <= 3: print(f"  실패 {r.wav_id}: {str(e)[:90]}")
        if (i + 1) % 500 == 0:
            el = time.time() - t0
            print(f"  {i+1:,}/{len(df):,}  ({el/(i+1)*1000:.0f}ms/개, "
                  f"남은 시간 ~{el/(i+1)*(len(df)-i-1)/60:.0f}분)", flush=True)

    if not ids: sys.exit("추출된 게 없습니다.")
    X = np.stack(feats)
    out = args.out or os.path.join(work, "e2v_feats.npz")
    np.savez_compressed(out, wav_id=np.array(ids), feats=X,
                        zs_label=np.array([x if x else "" for x in zs_lab]),
                        zs_conf=np.array(zs_conf, dtype=np.float32),
                        model=args.model)
    print(f"\n[saved] {out}")
    print(f"  {X.shape[0]:,}개 × {X.shape[1]}차원 · 실패 {failed}개 · {(time.time()-t0)/60:.1f}분")

    # ---- 4) 제로샷 점수 (라벨이 나온 모델일 때) ----
    valid = [i for i, l in enumerate(zs_lab) if l] if "label" in df.columns else []
    if valid:
        from sklearn.metrics import recall_score, accuracy_score
        sub = df.set_index(df.wav_id.astype(str)).loc[ids]
        y = sub.label.values[valid]
        p = np.array(zs_lab, dtype=object)[valid]
        te = sub.split.values[valid] == "test"
        print(f"\n=== emotion2vec 제로샷 (학습 없이) ===")
        for name, msk in (("전체", np.ones(len(y), bool)), ("test split", te)):
            if msk.sum() == 0: continue
            print(f"  {name:10s} n={msk.sum():,}  "
                  f"UAR {recall_score(y[msk], p[msk], average='macro', zero_division=0):.4f}  "
                  f"ACC {accuracy_score(y[msk], p[msk]):.4f}")
        print("  -> 우리 파인튜닝 모델과 비교하면 '데이터로 학습한 효과'가 나옵니다.")


if __name__ == "__main__":
    main()
