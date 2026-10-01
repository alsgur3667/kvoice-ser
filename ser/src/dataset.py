# -*- coding: utf-8 -*-
"""4단계: Dataset / Augmentation / Collate"""
import os, random
import numpy as np, pandas as pd, soundfile as sf, torch
from torch.utils.data import Dataset, WeightedRandomSampler


class SERDataset(Dataset):
    def __init__(self, df, cfg, split, train=False):
        # split="all" 은 분할 없이 전체를 쓴다. 외부 코퍼스 평가용.
        self.df = (df if split == "all" else df[df.split == split]).reset_index(drop=True)
        self.cfg, self.train = cfg, train
        self.classes = cfg["label"]["classes"]
        self.c2i = {c: i for i, c in enumerate(self.classes)}
        self.sr = cfg["audio"]["sample_rate"]
        self.max_len = int(cfg["audio"]["max_sec"] * self.sr)
        self.aug = cfg["augment"]
        self.soft_cols = [f"p_{c}" for c in self.classes]

    def __len__(self):
        return len(self.df)

    def _augment(self, y):
        a = self.aug
        if a.get("speed_perturb"):                       # 속도 변조 = 화자/발화속도 다양화
            sp = random.choice(a["speed_perturb"])
            if sp != 1.0:
                idx = np.round(np.arange(0, len(y), sp)).astype(int)
                y = y[idx[idx < len(y)]]
        if a.get("gain_db"):                             # 음량 변조
            y = y * (10 ** (random.uniform(*a["gain_db"]) / 20))
        if random.random() < a.get("noise_prob", 0):     # 가우시안 노이즈 (콜센터 환경 모사)
            snr = random.uniform(*a["noise_snr_db"])
            p = (y ** 2).mean()
            y = y + np.random.randn(len(y)).astype(np.float32) * np.sqrt(p / (10 ** (snr / 10)))
        return np.clip(y, -1, 1).astype(np.float32)

    def __getitem__(self, i):
        r = self.df.iloc[i]
        p = r.cache_path
        y = np.load(p).astype(np.float32) if p.endswith(".npy") else sf.read(p, dtype="float32")[0]
        if self.train:
            y = self._augment(y)
            if len(y) > self.max_len:                    # 학습은 랜덤 crop
                s = random.randint(0, len(y) - self.max_len); y = y[s:s + self.max_len]
        else:
            if len(y) > self.max_len:                    # 평가는 중앙 crop (재현성)
                s = (len(y) - self.max_len) // 2; y = y[s:s + self.max_len]
        return {
            "wave": torch.from_numpy(y),
            "y": torch.tensor(self.c2i[r.label], dtype=torch.long),
            "soft": torch.tensor(r[self.soft_cols].values.astype(np.float32)),
            "wav_id": str(r.wav_id),
        }


def collate(batch):
    L = max(b["wave"].shape[0] for b in batch)
    x = torch.zeros(len(batch), L)
    mask = torch.zeros(len(batch), L, dtype=torch.long)
    for i, b in enumerate(batch):
        n = b["wave"].shape[0]; x[i, :n] = b["wave"]; mask[i, :n] = 1
    return {
        "input_values": x,
        "attention_mask": mask,
        "y": torch.stack([b["y"] for b in batch]),
        "soft": torch.stack([b["soft"] for b in batch]),
        "wav_id": [b["wav_id"] for b in batch],
    }


def balanced_sampler(ds):
    """클래스 불균형 13.6:1 -> 역빈도 가중 샘플링"""
    y = ds.df.label.map(ds.c2i).values
    cnt = np.bincount(y, minlength=len(ds.classes)).astype(float)
    w = (1.0 / np.maximum(cnt, 1))[y]
    return WeightedRandomSampler(torch.DoubleTensor(w), len(w), replacement=True)
