# -*- coding: utf-8 -*-
from typing import Dict, List, Optional
from pydantic import BaseModel


class AnalysisCreated(BaseModel):
    id: str
    status: str


class Segment(BaseModel):
    idx: int
    t_start: float
    emotion: str
    confidence: float
    hold: bool
    valence: float
    arousal: float
    probs: Dict[str, float]
    probs_raw: Dict[str, float]


class Analysis(BaseModel):
    id: str
    created_at: Optional[str] = None
    status: str
    error: Optional[str] = None
    filename: Optional[str] = None
    duration_sec: Optional[float] = None
    domain: str
    region: str
    region_used: Optional[str] = None
    threshold: Optional[float] = None
    model_version: Optional[str] = None
    n_windows: Optional[int] = None
    hold_ratio: Optional[float] = None
    flow: Optional[str] = None
    transitions: Optional[int] = None
    risk_seconds: Optional[int] = None
    top_emotion: Optional[str] = None
    summary: Optional[dict] = None
    segments: List[Segment] = []


class FeedbackIn(BaseModel):
    analysis_id: str
    segment_idx: int
    said: str
    correct: str
    note: Optional[str] = None
