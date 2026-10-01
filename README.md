# 보이스 코리안 — 말투에서 감정을 읽는 AI

> 글자가 아니라 **말투**로 감정을 읽고, 3분짜리 통화에서 **언제 틀어졌는지** 찾아주는 서비스
> 팀 K-Voice (2인) · 2026.09.14 ~ 09.30 (16일)

한국어 음성에서 7감정을 인식하고, 통화를 **3초 단위로 잘라 감정 흐름을 그려주는** 웹 서비스입니다.
그래프에서 틀어진 지점을 클릭하면 **그 구간부터 재생**되어, 3분을 다 듣지 않아도 10초면 확인할 수 있습니다.

## 핵심 결과

| | |
|---|---|
| 주 지표 | **UAR** (클래스 평균 재현율) — 불균형 13.6:1 데이터라 정확도는 속인다 |
| 최종 성능 | 전체 test(n=4,840) **UAR 0.695 / WAR 0.721** |
| 판단 보류 허용 시 | 정확도 **90.1%** (신뢰도 0.70 이상 구간, 커버리지 50.3%) |
| 서비스 실측 | 69초 통화 → 45구간 · **추론 36.8초** (CPU, RTF 0.53) |
| 경량화 | fp32 380MB → **int8 197MB** |

## 이 프로젝트에서 가장 중요한 발견

**데이터에 붙어 있던 라벨이 정답이 아니었습니다.**

CSV의 `상황` 컬럼은 성우에게 준 **연기 지시**였고, 평가자 5명이 실제로 느낀 감정과 **68.1%만 일치**했습니다.

- 혐오로 연기한 것의 **48%만** 혐오로 들렸고, 16%는 분노로
- 놀람으로 연기한 것의 **38%는 그냥 중립**으로 들렸습니다

그대로 학습했다면 모델이 아니라 **데이터가 틀린 상태**로 끝까지 갔을 것입니다.
→ 라벨을 **5명 다수결(hard) + 투표 분포(soft)** 로 재정의했습니다.

## 기술 스택

**모델·학습** Python · PyTorch · HuggingFace Transformers(**WavLM-base-plus**) · torchaudio · TensorBoard
**데이터** pandas · NumPy · librosa/soundfile · scikit-learn
**서비스** FastAPI · Uvicorn · Pydantic · **Supabase**(PostgreSQL·Storage) · **Docker Compose** · nginx
**프런트** HTML/CSS · Vanilla JS · anime.js

## 구조

```
브라우저 → nginx(web) ─/api/→ FastAPI(api) → Supabase (Storage + Postgres)
                                                  ↑ 대기열에서 집어감
                                            worker (WavLM 추론)
```

컨테이너 3개가 `docker compose up` 한 번에 뜹니다. 업로드는 즉시 응답하고 무거운 추론은 워커가 뒤에서 처리합니다.
별도 큐 서버 없이 **DB의 status 컬럼을 큐로 사용**해, 컨테이너가 죽어도 재시작하면 이어서 처리됩니다.

## 모델

```
16kHz 파형(최대 8초)
 → CNN 인코더(동결) → 트랜스포머 12층(WavLM-base-plus)
 → 13개 층 출력의 가중합 → Attentive Statistics Pooling
 → 헤드 256 → 7감정 확률
```
총 9,497만 파라미터 · CB-Focal + soft KL · bf16 · RTX 4090

## 실험 비교

**고신뢰 test (n=3,329)**

| 접근 | UAR |
|---|---|
| 랜덤 (7클래스) | 0.143 |
| emotion2vec+ large 프리즈 | 0.287 |
| emotion2vec_base 프리즈 | 0.573 |
| **WavLM-base-plus 파인튜닝 (기준 모델)** | **0.734** |
| 앙상블 (내부 1위, 외부 검증 이득 0 → 기각) | 0.745 |

**전체 test (n=4,840)** — 위와 시험지가 달라 직접 비교 불가

| 모델 | UAR | WAR |
|---|---|---|
| full_1731 | 0.6754 | 0.7145 |
| mix40k (+SKT 4만) | 0.6626 | 0.7302 |
| **mix40k + 로짓 보정 τ=0.6 (서빙 모델)** | **0.6945** | **0.7211** |

> 점수 1위(앙상블 0.745)를 **버렸습니다.** 내부 +0.011인데 외부 검증 이득이 0이라 복잡도를 감수할 근거가 없었습니다.

## 문서

| 문서 | 내용 |
|---|---|
| [결과 보고서](docs/01_결과보고서.md) | 문제 정의 · 데이터 · 모델 · 검증 · 서비스 전체 |
| [개발 기록 1부](docs/02_개발기록_1부.md) | 9/14~9/21 · EDA, 백본 비교, 대화 흐름 실측 |
| [개발 기록 2부](docs/03_개발기록_2부.md) | 9/22~9/23 · 서버 학습, 로짓 보정, 중립 구조 분석 |
| [개발 기록 3부](docs/04_개발기록_3부.md) | 9/24~9/29 · 서비스 구현, 모니터링, 발표 준비 |
| [최종 정리](docs/05_최종정리.md) | 전체를 인과로 연결한 이해용 문서 |
| [회고](docs/06_회고록.md) | 막혔다 풀린 8건의 공통점, 발표 회고 |

## 폴더

```
ser/       학습 파이프라인 (EDA · 전처리 · 학습 · 평가 · 경량화)
service/   서비스 (FastAPI · worker · web · Docker Compose · Supabase 스키마)
docs/      보고서 · 개발 기록 · 회고
deck/      발표자료 (단일 HTML 33장 + 생성 코드)
```

## 실행

**학습**
```bash
cd ser
pip install -r requirements.txt
python src/build_manifest.py      # manifest 생성
python src/preprocess_audio.py    # 16kHz 캐시
python src/split.py               # 화자 독립 분할
python src/train.py --config configs/pilot.yaml
python src/evaluate.py --ckpt work/ckpt/pilot/best.pt
```

**서비스**
```bash
cd service
cp .env.example .env              # Supabase 키·모델 경로 입력
docker compose up -d              # api · worker · web
curl localhost:8000/system        # 컨테이너·모델·큐 상태
```

## 포함하지 않은 것

- **음성 데이터** — AI-Hub·SKT 코퍼스는 라이선스상 재배포할 수 없습니다
- **학습된 체크포인트** (`best.pt`, 380MB) — 용량 문제로 제외
- **`.env`** — Supabase 키 등 비밀값. `.env.example`을 참고해 직접 채우세요

## 한계

- **성우가 연기한 감정으로 배웠습니다.** 실제 통화의 흐릿한 말투는 배운 적이 없습니다
- **화자가 111명뿐**(학습 79명, 여성 73%). SKT를 섞어도 화자는 8명 늘었을 뿐입니다
- **전화망 8kHz·잡음 환경은 아직 평가하지 못했습니다**
- 보류 없이 전부 판정하면 오답률 27.9%입니다

세 가지가 전부 **데이터에서 온 한계**입니다. 그래서 모델을 키우는 대신, 화면의 오분류 신고가 쌓여 **누적 30건마다 재학습**되는 구조를 서비스에 넣었습니다.

---

**팀** K-Voice · 고민혁 · 정해운
