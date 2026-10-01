# -*- coding: utf-8 -*-
"""SKT 감정 TTS 코퍼스 -> 우리 manifest 포맷

데이터 생김새:
    <root>/<SPK>/[<SPK>/]script.txt          <- 중첩이 화자마다 다르다
    <root>/<SPK>/[<SPK>/]wav_48000/<SPK>_000001.wav

script.txt 한 덩어리:
    M0001_000001 NEUTRAL #지문
    전화가 끊어지자|||M 한숨을 내쉬는 대규||||HL      <- 원문 + 억양표기
    저놔가 끄너지자|||M 한수믈 네쉬는 데규||||HL      <- 발음 전사
    (빈 줄)

우리가 쓰는 것: wav_id, 화자, 성별, 감정 라벨.  텍스트는 쓰지 않는다(원칙 1).

주의할 점 세 가지 — 실제로 데이터를 뜯어보고 확인한 것들이다:
  1) M0004 의 script.txt 는 라벨 문자가 깨져 있다. H/L 이 빠진다.
     NEUTRAL->NEUTRA, SHY->SY, HURRY->URRY, HESITATE->ESITATE, UNPLEASURE->UNPEASURE
     확인된 것만 5,396건. 정규화하지 않으면 라벨이 21종으로 늘어난다.
  2) 폴더 중첩이 화자마다 다르다. M0001/M0001/script.txt 인데 M0004/script.txt 다.
  3) 16종 라벨 중 우리 7클래스에 정확히 대응하는 건 7종뿐이다(전체의 54%).
     나머지를 어떻게 할지가 이 데이터의 핵심 설계 결정이라 --map 으로 골라야 한다.

  python src/skt_manifest.py --config configs/skt.yaml --map strict
"""
import argparse, os, re, sys, glob, collections
import pandas as pd, yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wpath import wp

CANON = ["NEUTRAL", "ANGRY", "SAD", "JOY", "ANXIOUS", "KIND", "TEASE", "DRY",
         "SURPRISE", "SERIOUS", "DOUBT", "SHY", "HURRY", "FEAR", "UNPLEASURE",
         "HESITATE"]

# 7클래스 매핑 세 가지. 어느 걸 쓰느냐로 데이터 양과 불균형비가 크게 달라진다.
MAPS = {
    # 정확히 대응하는 것만. 가장 안전하지만 46%를 버린다.
    "strict": {
        "NEUTRAL": "neutral", "ANGRY": "angry", "SAD": "sadness", "JOY": "happy",
        "SURPRISE": "surprise", "FEAR": "fear", "UNPLEASURE": "disgust",
    },
    # + 근거 있는 인접 감정. ANXIOUS(불안)는 FEAR 와 같은 고각성 부정이고,
    #   FEAR 가 412개뿐이라 이걸 합치지 않으면 fear 클래스는 사실상 학습이 안 된다.
    #   DRY(무미건조) / SERIOUS(진지)는 각성도가 낮고 방향성이 없어 neutral 에 가깝다.
    "extended": {
        "NEUTRAL": "neutral", "ANGRY": "angry", "SAD": "sadness", "JOY": "happy",
        "SURPRISE": "surprise", "FEAR": "fear", "UNPLEASURE": "disgust",
        "ANXIOUS": "fear", "DRY": "neutral", "SERIOUS": "neutral",
    },
    # 전부 욱여넣는다. 데이터는 최대지만 neutral 이 오염되고 라벨 정의가 흐려진다.
    "all": {
        "NEUTRAL": "neutral", "ANGRY": "angry", "SAD": "sadness", "JOY": "happy",
        "SURPRISE": "surprise", "FEAR": "fear", "UNPLEASURE": "disgust",
        "ANXIOUS": "fear", "DRY": "neutral", "SERIOUS": "neutral",
        "KIND": "happy", "TEASE": "disgust", "DOUBT": "neutral",
        "SHY": "neutral", "HURRY": "neutral", "HESITATE": "neutral",
    },
}

HDR = re.compile(r"^([FM]\d{4})_(\d{6})\s+(\S+)\s*(.*)$")


def is_subseq(short, long_):
    """short 의 글자들이 long_ 안에 순서대로 등장하는가."""
    it = iter(long_)
    return all(c in it for c in short)


def normalize_label(raw, unknown_counter):
    """깨진 라벨을 원래 라벨로 되돌린다."""
    u = raw.upper()
    if u in CANON:
        return u
    # 글자가 빠진 경우: 원본 라벨의 부분수열이면서 길이차가 2 이하인 후보를 찾는다
    cands = [c for c in CANON if len(c) - len(u) in (1, 2) and is_subseq(u, c)]
    if len(cands) == 1:
        return cands[0]
    unknown_counter[raw] += 1
    return None


def parse_script(path, spk):
    """script.txt -> [(wav_id, 감정, 스타일태그)]"""
    out = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = HDR.match(line.rstrip("\n"))
            if m and m.group(1) == spk:
                out.append((f"{m.group(1)}_{m.group(2)}", m.group(3), m.group(4).strip()))
    return out


def find_speakers(root):
    """<root> 아래 화자별 (spk, script.txt, wav폴더) 를 찾는다. 중첩 깊이가 제각각이라 glob 으로 훑는다."""
    found = {}
    for s in glob.glob(os.path.join(root, "**", "script.txt"), recursive=True):
        d = os.path.dirname(s)
        wav = os.path.join(d, "wav_48000")
        if not os.path.isdir(wav):
            continue
        # 화자 id 는 wav 파일 이름에서 가져온다. 폴더 이름보다 믿을 만하다.
        sample = next(iter(sorted(os.listdir(wav))), None)
        if not sample:
            continue
        spk = sample.split("_")[0]
        if spk in found:
            print(f"[warn] 화자 {spk} 중복 — 먼저 찾은 것 유지: {found[spk][0]}")
            continue
        found[spk] = (s, wav)
    return dict(sorted(found.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/skt.yaml")
    ap.add_argument("--root", default=None, help="SKT large 폴더. 없으면 config 의 raw_root")
    ap.add_argument("--map", default="strict", choices=list(MAPS))
    ap.add_argument("--label-conf", type=float, default=1.0,
                    help="soft 타깃에서 정답 클래스에 줄 확률. 1.0 = one-hot. "
                         "SKT 라벨은 청취 검증이 없는 '연기 지시'라 0.7 정도로 "
                         "낮춰 불확실성을 반영하는 것도 방법이다.")
    ap.add_argument("--check-wav", action="store_true", default=True)
    ap.add_argument("--no-check-wav", dest="check_wav", action="store_false")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    classes = cfg["label"]["classes"]
    root = args.root or cfg["paths"]["raw_root"]
    work = cfg["paths"]["work_root"]
    os.makedirs(work, exist_ok=True)

    if not os.path.isdir(root):
        sys.exit(f"[FAIL] 없는 경로: {root}")

    spks = find_speakers(root)
    if not spks:
        sys.exit(f"[FAIL] {root} 아래에서 script.txt + wav_48000 짝을 못 찾았습니다")
    print(f"[화자] {len(spks)}명: {', '.join(spks)}\n")

    unknown = collections.Counter()
    fixed = collections.Counter()
    rows, raw_counts = [], collections.Counter()

    for spk, (script, wavdir) in spks.items():
        have = set(os.listdir(wavdir)) if args.check_wav else None
        items = parse_script(script, spk)
        miss = 0
        for wid, raw, style in items:
            lab = normalize_label(raw, unknown)
            if lab is None:
                continue
            if lab != raw.upper():
                fixed[f"{raw} -> {lab}"] += 1
            raw_counts[lab] += 1
            fn = f"{wid}.wav"
            if have is not None and fn not in have:
                miss += 1
                continue
            rows.append(dict(
                wav_id=f"SKT_{wid}",
                wav_path=os.path.join(wavdir, fn),
                src="skt_large",
                spk=spk,                       # 진짜 화자 id. AI-Hub 처럼 추정할 필요가 없다
                age="unknown",
                gender="남" if spk[0] == "M" else "여",
                emo16=lab,                     # 원본 16종 (메타데이터)
                style_tag=style,               # #지문 / #화가난듯 ... (메타데이터)
                                               # 이름이 style 이면 안 된다: DataFrame.style 은
                                               # pandas 의 Styler 속성이라 컬럼이 가려진다
            ))
        print(f"  {spk}  스크립트 {len(items):>6,}행" + (f"  · wav 없음 {miss:,}" if miss else ""))

    if fixed:
        print(f"\n[라벨 정규화] 깨진 라벨 {sum(fixed.values()):,}건을 되돌렸습니다")
        for k, v in fixed.most_common():
            print(f"    {k:<28} {v:>6,}")
    if unknown:
        print(f"\n[warn] 해석 못 한 라벨 {sum(unknown.values()):,}건 (버립니다)")
        for k, v in unknown.most_common(10):
            print(f"    {k!r:<20} {v:>6,}")

    df = pd.DataFrame(rows)
    if df.empty:
        sys.exit("[FAIL] 만들어진 행이 없습니다")

    # ---- 매핑 3종 비교표. 어느 걸 쓸지는 숫자를 보고 정한다 ----
    print(f"\n{'='*70}\n  매핑별 결과 비교  (총 {len(df):,}발화)\n{'='*70}")
    hdr = f"  {'클래스':<10}" + "".join(f"{k:>14}" for k in MAPS)
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    tabs = {k: df.emo16.map(v).value_counts() for k, v in MAPS.items()}
    for c in classes:
        print(f"  {c:<10}" + "".join(f"{int(tabs[k].get(c,0)):>14,}" for k in MAPS))
    print("  " + "-" * (len(hdr) - 2))
    print(f"  {'사용':<10}" + "".join(f"{int(tabs[k].sum()):>14,}" for k in MAPS))
    print(f"  {'버림':<10}" + "".join(f"{len(df)-int(tabs[k].sum()):>14,}" for k in MAPS))
    print(f"  {'불균형비':<10}" + "".join(
        f"{tabs[k].max()/max(tabs[k].min(),1):>13.1f}:1" for k in MAPS))

    # ---- 선택한 매핑 적용 ----
    df["label"] = df.emo16.map(MAPS[args.map])
    before = len(df)
    df = df[df.label.notna()].reset_index(drop=True)
    print(f"\n[선택] --map {args.map}  ->  {len(df):,}행 사용 "
          f"({len(df)/before*100:.1f}%), {before-len(df):,}행 제외")

    # ---- soft 타깃 ----
    # AI-Hub 는 평가자 5명 투표분포가 있어서 진짜 soft 라벨이 나온다.
    # SKT 는 지시 하나뿐이라 one-hot 이 원칙인데, 그러면 "이 라벨은 확실하다"고
    # 모델에게 가르치는 셈이 된다. label-conf 로 그 확신을 낮출 수 있다.
    k = len(classes)
    conf = min(max(args.label_conf, 1.0 / k), 1.0)
    rest = (1.0 - conf) / (k - 1)
    for i, c in enumerate(classes):
        df[f"p_{c}"] = (df.label == c).map({True: conf, False: rest})
    df["n_votes"] = 1          # 평가자 1명(=연기 지시). AI-Hub 의 5명과 구분된다
    df["entropy"] = 0.0
    # 메타데이터로만 남긴다. dataset.py 는 이 컬럼을 읽지 않는다(원칙 1, 2).
    df["scenario"] = df["emo16"].astype(str) + " " + df["style_tag"].astype(str)

    keep = ["wav_id", "wav_path", "src", "spk", "age", "gender", "label",
            "n_votes", "entropy", "scenario"] + [f"p_{c}" for c in classes]
    out = df[keep]
    path = wp(cfg, "manifest.csv")
    out.to_csv(path, index=False, encoding="utf-8-sig")

    print(f"\n[saved] {path}  ({len(out):,}행)")
    print("\n화자별 분포:\n", pd.crosstab(out.spk, out.label))
    print(f"\nsoft 타깃: 정답 {conf:.3f} / 나머지 각 {rest:.3f}"
          + ("  (one-hot)" if conf >= 0.999 else "  <- 라벨 불확실성 반영"))
    print("\n다음 단계:")
    print(f"  python src/preprocess_audio.py --config {args.config} --workers 32")
    print(f"  python src/split.py            --config {args.config}")


if __name__ == "__main__":
    main()
