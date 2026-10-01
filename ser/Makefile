SHELL := /bin/bash
CKPT ?= work/ckpt/best.pt
DATA ?= ./data

.PHONY: help bake demo build-demo train save load clean

help:
	@echo "make bake CKPT=work/ckpt/0915_1200/best.pt   # 체크포인트를 이미지에 구울 위치로 복사"
	@echo "make demo                                    # 데모 빌드+기동 (http://localhost:8000)"
	@echo "make train DATA=/path/to/dataset SER_GPUS=2  # 학습 컨테이너 실행"
	@echo "make save                                    # ser-demo.tar 로 내보내기 (USB/오프라인 발표용)"
	@echo "make load                                    # tar 에서 이미지 복원"

bake:
	@mkdir -p model
	@cp "$(CKPT)" model/best.pt
	@ls -lh model/best.pt

build-demo:
	docker compose build demo

demo: build-demo
	docker compose up -d demo
	@echo "-> http://localhost:8000  (기동까지 30~60초, docker compose logs -f demo 로 확인)"

train:
	SER_DATA="$(DATA)" docker compose --profile train run --rm train all

save:
	docker save ser-demo:1.0 -o ser-demo.tar
	@ls -lh ser-demo.tar

load:
	docker load -i ser-demo.tar

clean:
	docker compose down -v
