# -*- coding: utf-8 -*-
"""5단계: 모델 — 사전학습 음성 인코더 + Attentive Statistics Pooling 헤드

왜 MFCC+LSTM 을 안 쓰나:
  44k개 / 45시간은 밑바닥부터 배우기엔 작다. 자기지도 사전학습 모델(WavLM/wav2vec2)은
  수만 시간 음성으로 이미 운율·음색 표현을 배워놨고, SER 벤치마크에서 MFCC 계열 대비
  UAR 기준 통상 +10~20%p 높다. 우리가 할 일은 파인튜닝뿐.
"""
import torch, torch.nn as nn
from transformers import AutoModel, AutoConfig


class AttentiveStatPool(nn.Module):
    """프레임별 중요도를 학습해 가중 평균+표준편차로 요약.
    감정은 발화 전체가 아니라 특정 구간(어미 억양, 강세)에 몰려 있어 mean pooling 보다 낫다."""
    def __init__(self, d, h=128):
        super().__init__()
        self.att = nn.Sequential(nn.Conv1d(d, h, 1), nn.Tanh(), nn.Conv1d(h, d, 1))

    def forward(self, x, mask=None):            # x: (B,T,D)
        x = x.transpose(1, 2)                   # (B,D,T)
        w = self.att(x)
        if mask is not None:
            w = w.masked_fill(~mask.unsqueeze(1).bool(), -1e4)
        w = torch.softmax(w, dim=-1)
        mu = (x * w).sum(-1)
        sd = torch.sqrt(((x ** 2) * w).sum(-1) - mu ** 2 + 1e-6)
        return torch.cat([mu, sd], -1)          # (B, 2D)


class SERModel(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        m = cfg["model"]; n_cls = len(cfg["label"]["classes"])
        self.backbone = AutoModel.from_pretrained(m["backbone"])
        d = self.backbone.config.hidden_size

        if m.get("freeze_feature_encoder", True):
            if hasattr(self.backbone, "freeze_feature_encoder"):
                self.backbone.freeze_feature_encoder()
        for i in range(m.get("freeze_first_n_layers", 0)):
            for p in self.backbone.encoder.layers[i].parameters():
                p.requires_grad = False

        if m.get("use_lora"):                    # large 백본을 8GB에 올릴 때
            from peft import LoraConfig, get_peft_model
            self.backbone = get_peft_model(self.backbone, LoraConfig(
                r=m["lora_r"], lora_alpha=m["lora_r"] * 2, lora_dropout=0.05,
                target_modules=["q_proj", "k_proj", "v_proj", "out_proj"], bias="none"))

        # LayerDrop 끄기 — 필수.
        # wav2vec2/WavLM 은 학습 모드에서 레이어를 확률적으로 건너뛰는데(layerdrop),
        # 그러면 반환되는 hidden_states 개수가 매 step 달라져 레이어 가중합이 깨진다.
        # 파인튜닝에선 어차피 끄는 게 표준이다.
        for obj in (self.backbone.config, getattr(self.backbone, "encoder", None)):
            if obj is not None and hasattr(obj, "layerdrop"):
                obj.layerdrop = 0.0
            if obj is not None and hasattr(obj, "config") and hasattr(obj.config, "layerdrop"):
                obj.config.layerdrop = 0.0

        # 레이어별 가중합 — 감정 정보는 마지막 층이 아니라 중간층(6~9)에 가장 많다.
        # hidden_states 길이는 라이브러리 버전에 따라 L 또는 L+1 이라 실측한다.
        was_training = self.backbone.training
        self.backbone.train()
        with torch.no_grad():
            hs = self.backbone(torch.zeros(1, 4000),
                               output_hidden_states=True).hidden_states
        self.backbone.train(was_training)
        if hs is None or len(hs) == 0:
            raise RuntimeError("백본이 hidden_states 를 반환하지 않습니다.")
        self.n_layers = len(hs)
        self.layer_w = nn.Parameter(torch.zeros(self.n_layers))

        self.pool = AttentiveStatPool(d) if m["pooling"] == "attentive_stat" else None
        pd_ = d * 2 if self.pool else d
        self.head = nn.Sequential(
            nn.Linear(pd_, m["head_hidden"]), nn.LayerNorm(m["head_hidden"]),
            nn.GELU(), nn.Dropout(m["dropout"]), nn.Linear(m["head_hidden"], n_cls))

    def forward(self, input_values, attention_mask=None):
        out = self.backbone(input_values, attention_mask=attention_mask,
                            output_hidden_states=True)
        states = out.hidden_states
        if states is not None and len(states) == self.n_layers:
            hs = torch.stack(states, 0)                        # (L,B,T,D)
            h = (torch.softmax(self.layer_w, 0).view(-1, 1, 1, 1) * hs).sum(0)
        else:                                                   # 안전망
            h = out.last_hidden_state

        fmask = None
        if attention_mask is not None and hasattr(self.backbone, "_get_feat_extract_output_lengths"):
            fl = self.backbone._get_feat_extract_output_lengths(attention_mask.sum(-1)).long()
            fmask = (torch.arange(h.size(1), device=h.device)[None, :] < fl[:, None])

        z = self.pool(h, fmask) if self.pool else (
            h.mean(1) if fmask is None else
            (h * fmask.unsqueeze(-1)).sum(1) / fmask.sum(1, keepdim=True).clamp(min=1))
        return self.head(z)


def param_groups(model, cfg):
    bb = [p for n, p in model.named_parameters() if n.startswith("backbone") and p.requires_grad]
    hd = [p for n, p in model.named_parameters() if not n.startswith("backbone") and p.requires_grad]
    return [{"params": bb, "lr": cfg["train"]["lr_backbone"]},
            {"params": hd, "lr": cfg["train"]["lr_head"]}]
