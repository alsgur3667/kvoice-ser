# -*- coding: utf-8 -*-
"""
이미 끝난 학습의 콘솔 출력을 TensorBoard 로 복원한다.

TensorBoard 를 붙이기 전에 돌린 학습(pilot 등)은 곡선이 안 남아 있다.
cmd 스크롤백을 텍스트 파일로 저장해서 넣으면 epoch 곡선을 만들어준다.

사용:
  1) cmd 창 우클릭 -> 모두 선택 -> Enter (복사됨) -> 메모장에 붙여넣고 log.txt 로 저장
  2) python src\\tb_from_log.py --log log.txt --run pilot_1006
"""
import argparse, os, re, sys

EP = re.compile(r"\[ep(\d+)\]\s+(\d+)s\s+loss\s+([\d.]+)\s*\|\s*"
                r"UAR\s+([\d.]+)\s+WAR\s+([\d.]+)\s+F1\s+([\d.]+)")
ST = re.compile(r"ep(\d+)\s+(\d+)/(\d+)\s+loss\s+([\d.]+)\s+lr\s+([\d.e+-]+)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--run", required=True, help="체크포인트 폴더명 (예: pilot_1006)")
    ap.add_argument("--work", default="./work")
    args = ap.parse_args()

    try:
        from torch.utils.tensorboard import SummaryWriter
    except Exception:
        sys.exit("pip install tensorboard 먼저 하세요.")

    text = open(args.log, encoding="utf-8", errors="replace").read()
    eps = EP.findall(text)
    sts = ST.findall(text)
    if not eps and not sts:
        sys.exit("로그에서 학습 기록을 못 찾았습니다. '[ep0] ... UAR ...' 줄이 있는지 확인하세요.")

    tb_dir = os.path.join(args.work, "tb", args.run)
    w = SummaryWriter(tb_dir)

    for ep, sec, loss, uar, war, f1 in eps:
        e = int(ep)
        w.add_scalar("train/loss_epoch", float(loss), e)
        w.add_scalar("val/UAR", float(uar), e)
        w.add_scalar("val/WAR_accuracy", float(war), e)
        w.add_scalar("val/macroF1", float(f1), e)
        w.add_scalar("time/epoch_sec", float(sec), e)

    for ep, i, total, loss, lr in sts:
        gs = int(ep) * int(total) + int(i)
        w.add_scalar("train/loss_step", float(loss), gs)
        w.add_scalar("train/lr_backbone", float(lr), gs)

    w.add_text("run/출처", f"콘솔 로그에서 복원됨 ({args.log})", 0)
    w.close()
    print(f"복원 완료: epoch {len(eps)}개 / step {len(sts)}개")
    print(f"[tb] {tb_dir}")
    print(f"     tensorboard --logdir {os.path.join(args.work, 'tb')}")


if __name__ == "__main__":
    main()
