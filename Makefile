.PHONY: help pipeline embed freq similarity extract build clean test td td-sample td-sample-peek

help:
	@echo "📦 Heritage Archive — 파이프라인 명령어"
	@echo ""
	@echo "전체 파이프라인:"
	@echo "  make pipeline              전체 실행 (임베딩 → 형태소 → 유사도 → 태그 → 빌드)"
	@echo "  make quick                 빠른 재빌드 (API 스킵)"
	@echo ""
	@echo "개별 단계:"
	@echo "  make embed                 임베딩 생성 (Gemini)"
	@echo "  make freq                  형태소 분석"
	@echo "  make similarity            유사도 계산"
	@echo "  make extract               태그 추출 (Gemini)"
	@echo "  make build                 HTML 빌드"
	@echo ""
	@echo "task-discovery:"
	@echo "  make td-sample             합성 코퍼스로 산출물 한 벌 → data/td_sample/ (실데이터 무접촉)"
	@echo "  make td-sample-peek        샘플 산출물 상태 확인"
	@echo ""
	@echo "유틸:"
	@echo "  make test                  pytest 실행"
	@echo "  make screenshot            HTML 스크린샷 (headless Chrome)"
	@echo "  make dummy                 더미 데이터 생성 후 빌드"
	@echo "  make clean                 dist/ data/*.json 제거"

pipeline:
	./scripts/pipeline.sh

quick:
	./scripts/pipeline.sh --skip-embed --skip-extract

embed:
	python3 scripts/embed.py

freq:
	python3 scripts/freq.py

similarity:
	python3 scripts/similarity.py

extract:
	GEMINI_API_KEY=${GEMINI_API_KEY} python3 scripts/run_extraction.py

build:
	python3 scripts/build.py

# SOURCES=data/persons.json 로 실데이터 추출 입력 지정 (미지정 시 합성 코퍼스)
td:
	GEMINI_API_KEY=${GEMINI_API_KEY} python3 scripts/td_pipeline.py $(SOURCES:%=--sources %)

# 합성 코퍼스로 산출물 한 벌 (#010). 출력·로그·콜덤프를 전부 data/td_sample/ 아래로 몰아
# 실데이터와 섞이지 않게 한다. 입력이 합성이라 이 디렉터리는 에이전트가 읽어도 된다.
TD_SAMPLE_DIR ?= data/td_sample

td-sample:
	TD_OUT_DIR=$(TD_SAMPLE_DIR) GEMINI_API_KEY=${GEMINI_API_KEY} \
	  python3 scripts/td_pipeline.py $(TD_SAMPLE_DIR)/task_discovery
	$(MAKE) td-sample-peek

td-sample-peek:
	TD_OUT_DIR=$(TD_SAMPLE_DIR) python3 scripts/td_peek.py $(TD_SAMPLE_DIR)/task_discovery

td-codebook:
	GEMINI_API_KEY=${GEMINI_API_KEY} python3 scripts/td_pipeline.py --codebook data/task_discovery/codebook.json $(SOURCES:%=--sources %)

td-search:
	GEMINI_API_KEY=${GEMINI_API_KEY} python3 scripts/td_pipeline.py --search $(SOURCES:%=--sources %)

test:
	python3 -m pytest tests/ -q

screenshot:
	@CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; \
	"$$CHROME" --headless=new --disable-gpu --window-size=1600,1000 --timeout=8000 \
	  --screenshot=/tmp/heritage-shot.png "file://$$(pwd)/dist/heritage-archive.html#view=cloudmax" && \
	echo "✓ Screenshot: /tmp/heritage-shot.png"

dummy:
	python3 scripts/generate_dummy.py
	make quick

clean:
	rm -rf dist/
	rm -f data/embeddings.json data/neighbors.json data/freq.json data/tags.json

info:
	@echo "📋 현재 파일 상태:"
	@ls -lh data/*.json 2>/dev/null || echo "  (데이터 파일 없음)"
	@[ -f dist/heritage-archive.html ] && echo "  ✓ dist/heritage-archive.html" || echo "  ✗ dist/heritage-archive.html"
	@echo ""
	@echo "📊 더 자세한 가이드: scripts/PIPELINE.md"
