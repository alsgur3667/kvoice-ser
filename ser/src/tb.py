# -*- coding: utf-8 -*-
"""TensorBoard 유틸 — 스칼라 말고 '그림'까지 남긴다.
matplotlib 를 Agg 백엔드로 강제해서 서버/윈도우 어디서든 창 없이 동작."""
import io
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# 그림 안의 글자는 전부 영문으로 둔다 — 한글 폰트가 없는 환경에서 □□ 로 깨지는 걸 피함
matplotlib.rcParams["axes.unicode_minus"] = False


def _fig_to_chw(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    import matplotlib.image as mpimg
    img = mpimg.imread(buf)              # HWC, float 0~1
    if img.shape[2] == 4:
        img = img[:, :, :3]
    return np.transpose(img, (2, 0, 1))  # CHW


def confusion_figure(cm, classes, title="Confusion matrix (row-normalized %)"):
    cm = np.asarray(cm, dtype=float)
    norm = cm / np.maximum(cm.sum(1, keepdims=True), 1) * 100
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    im = ax.imshow(norm, cmap="Blues", vmin=0, vmax=100)
    ax.set_xticks(range(len(classes))); ax.set_xticklabels(classes, rotation=45, ha="right")
    ax.set_yticks(range(len(classes))); ax.set_yticklabels(classes)
    ax.set_xlabel("predicted"); ax.set_ylabel("true"); ax.set_title(title)
    for i in range(len(classes)):
        for j in range(len(classes)):
            v = norm[i, j]
            if v >= 0.5:
                ax.text(j, i, f"{v:.0f}", ha="center", va="center",
                        fontsize=8, color="white" if v > 55 else "black")
    fig.colorbar(im, ax=ax, shrink=.8)
    return _fig_to_chw(fig)


def per_class_figure(report, classes):
    """report: {cls: {'precision':..,'recall':..,'f1':..,'support':..}}"""
    x = np.arange(len(classes)); w = 0.27
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    for k, off, c in (("precision", -w, "#2a78d6"), ("recall", 0, "#eb6834"), ("f1", w, "#1baf7a")):
        ax.bar(x + off, [report[c_][k] for c_ in classes], w, label=k, color=c)
    ax.set_xticks(x); ax.set_xticklabels(
        [f"{c}\n(n={report[c]['support']})" for c in classes], fontsize=8)
    ax.set_ylim(0, 1); ax.set_ylabel("score"); ax.legend(fontsize=8, ncol=3)
    ax.set_title("Per-class precision / recall / F1")
    ax.grid(axis="y", alpha=.25, linewidth=.6); ax.set_axisbelow(True)
    return _fig_to_chw(fig)


def calibration_figure(conf, correct, bins=10):
    """신뢰도 보정 곡선. 대각선에 붙을수록 '모델이 자기 확신을 정직하게 말한다'."""
    conf = np.asarray(conf, float); correct = np.asarray(correct, float)
    edges = np.linspace(0, 1, bins + 1)
    xs, ys, ns = [], [], []
    for i in range(bins):
        m = (conf > edges[i]) & (conf <= edges[i + 1])
        if m.sum() == 0: continue
        xs.append(conf[m].mean()); ys.append(correct[m].mean()); ns.append(int(m.sum()))
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(5.4, 5.4),
                                 gridspec_kw={"height_ratios": [3, 1]}, sharex=True)
    a1.plot([0, 1], [0, 1], "--", color="#999", linewidth=1, label="perfect calibration")
    a1.plot(xs, ys, "o-", color="#2a78d6", linewidth=2, markersize=6, label="observed")
    a1.set_ylabel("accuracy"); a1.set_ylim(0, 1.02); a1.legend(fontsize=8)
    a1.set_title("Reliability diagram"); a1.grid(alpha=.25, linewidth=.6)
    a2.bar(xs, ns, width=.07, color="#86b6ef")
    a2.set_xlabel("model confidence"); a2.set_ylabel("samples"); a2.grid(alpha=.25, linewidth=.6)
    ece = sum(n * abs(y - x) for x, y, n in zip(xs, ys, ns)) / max(1, sum(ns))
    a1.text(.03, .93, f"ECE = {ece:.3f}", transform=a1.transAxes, fontsize=9)
    return _fig_to_chw(fig), ece
