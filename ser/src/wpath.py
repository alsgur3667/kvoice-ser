# -*- coding: utf-8 -*-
"""work/ 안의 manifest 파일 이름을 config 별로 분리한다.

왜 필요한가:
  train.bat 은 어떤 mode 를 돌리든 build_manifest -> preprocess -> split 을 다시 돈다.
  그런데 pilot/xlsr 계열은 min_votes=4 (고신뢰 서브셋), full 은 min_votes=2 (전체) 라서
  같은 manifest_split.csv 를 서로 덮어쓴다.
  -> xlsr 한 번 돌리면 full_1731 의 test set 이 조용히 바뀌어버린다.

해결:
  config 에 paths.tag 를 주면 manifest_split_<tag>.csv 처럼 접미사가 붙는다.
  tag 가 없으면 예전 이름 그대로라서 기존 체크포인트(full_1731)는 영향이 없다.
  체크포인트 안에 cfg 가 통째로 저장되므로 evaluate.py 는 자동으로 올바른 파일을 읽는다.

  오디오 캐시(work/audio_16000)는 tag 와 무관하게 공유된다. 전처리는 여전히 한 번만.
"""
import os


def tag_of(cfg):
    t = (cfg.get("paths") or {}).get("tag") or ""
    return f"_{t}" if t else ""


def wp(cfg, name):
    """work/<stem><_tag><ext> 경로를 돌려준다."""
    work = cfg["paths"]["work_root"]
    stem, ext = os.path.splitext(name)
    return os.path.join(work, f"{stem}{tag_of(cfg)}{ext}")
