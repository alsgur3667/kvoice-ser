# -*- coding: utf-8 -*-
"""불균형(13.6:1) + 라벨 노이즈 대응 손실"""
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F


class CBFocalLoss(nn.Module):
    """Class-Balanced Focal Loss (Cui et al. 2019)
       유효표본수 기반 가중 -> 단순 역빈도보다 과보정이 덜하다."""
    def __init__(self, counts, beta=0.999, gamma=1.5, smoothing=0.0):
        super().__init__()
        eff = 1.0 - np.power(beta, counts)
        w = (1.0 - beta) / np.maximum(eff, 1e-8)
        w = w / w.sum() * len(counts)
        self.register_buffer("w", torch.tensor(w, dtype=torch.float32))
        self.gamma, self.smoothing = gamma, smoothing

    def forward(self, logits, target):
        logp = F.log_softmax(logits, -1)
        if self.smoothing > 0:
            n = logits.size(-1)
            t = torch.full_like(logp, self.smoothing / (n - 1))
            t.scatter_(1, target[:, None], 1 - self.smoothing)
            ce = -(t * logp).sum(-1)
            pt = logp.gather(1, target[:, None]).squeeze(1).exp()
        else:
            ce = F.nll_loss(logp, target, reduction="none")
            pt = (-ce).exp()
        return (self.w[target] * ((1 - pt) ** self.gamma) * ce).mean()


class SoftKD(nn.Module):
    """평가자 5명 투표분포를 soft target 으로.
       '5명 중 3명만 슬픔'인 애매한 샘플에 100% 확신을 강요하지 않아 과적합이 줄고 보정이 좋아진다."""
    def forward(self, logits, soft):
        return F.kl_div(F.log_softmax(logits, -1), soft.clamp_min(1e-8), reduction="batchmean")


def build_loss(cfg, counts):
    kind = cfg["train"]["loss"]
    if kind == "cb_focal":
        hard = CBFocalLoss(counts, gamma=cfg["train"]["focal_gamma"],
                           smoothing=cfg["train"]["label_smoothing"])
    elif kind == "weighted_ce":
        w = torch.tensor((counts.sum() / np.maximum(counts, 1)), dtype=torch.float32)
        w = w / w.mean()
        hard = nn.CrossEntropyLoss(weight=w, label_smoothing=cfg["train"]["label_smoothing"])
    else:
        hard = nn.CrossEntropyLoss(label_smoothing=cfg["train"]["label_smoothing"])
    return hard, (SoftKD() if cfg["label"]["use_soft_label"] else None)
