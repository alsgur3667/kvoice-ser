# -*- coding: utf-8 -*-
"""환경변수 한 곳에서 읽기 (.env → 컨테이너 env)"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_bucket: str = "audio"

    mock: int = 1                 # 1이면 모델 없이 가짜 결과 (발표 안전장치)
    device: str = "cpu"
    ckpt_path: str = "/models/best.pt"
    ser_src: str = "/app/ser_src"

    win_sec: float = 3.0
    hop_sec: float = 1.5
    sample_rate: int = 16000
    max_duration_sec: int = 1800
    max_upload_mb: int = 100
    hold_threshold: float = 0.0       # >0 이면 현장별 기본 임계값 대신 이 값을 쓴다          # 업로드 용량 상한 (무료 터널 한도와 맞춤)

    worker_poll_sec: float = 2.0
    model_version: str = "wavlm-mix40k-tau0.6"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
