#!/bin/bash
# 전체 파이프라인 실행: 임베딩 → 형태소분석 → 유사도 → 태그추출 → 빌드
# 사용: ./scripts/pipeline.sh [--skip-embed] [--skip-extract]

set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

# 색상 출력
log_step() { echo "━━━ $1 ━━━"; }
log_done() { echo "✓ $1"; }
log_error() { echo "✗ $1" >&2; }

# 환경 변수 체크
check_env() {
    if [ -z "$GEMINI_API_KEY" ]; then
        log_error "GEMINI_API_KEY 환경변수 필요"
        exit 1
    fi
}

# 입력 파일 체크
check_input() {
    if [ ! -f "$ROOT/data/persons.json" ]; then
        log_error "data/persons.json 없음"
        exit 1
    fi
}

# 1. 임베딩 (Gemini)
run_embed() {
    log_step "1. 임베딩 생성 (Gemini)"
    check_env
    python3 "$ROOT/scripts/embed.py"
    log_done "embeddings.json 생성"
}

# 2. 형태소 분석 (Kiwi)
run_freq() {
    log_step "2. 형태소 분석 (명사 빈도)"
    python3 "$ROOT/scripts/freq.py"
    log_done "freq.json 생성"
}

# 3. 유사도 계산 (코사인)
run_similarity() {
    log_step "3. 유사도 계산 (상위 30명)"
    python3 "$ROOT/scripts/similarity.py"
    log_done "neighbors.json 생성"
}

# 4. 태그 추출 (Gemini)
run_extract() {
    log_step "4. 태그 추출 (LLM)"
    check_env
    python3 "$ROOT/scripts/run_extraction.py"
    log_done "tags.json 추출 완료"
}

# 5. 최종 빌드
run_build() {
    log_step "5. HTML 빌드 (인라인)"
    python3 "$ROOT/scripts/build.py"
    log_done "dist/heritage-archive.html 생성"
}

# 메인
main() {
    check_input

    skip_embed=false
    skip_extract=false

    # 옵션 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-embed) skip_embed=true; shift ;;
            --skip-extract) skip_extract=true; shift ;;
            *) echo "Unknown option: $1"; exit 1 ;;
        esac
    done

    echo "📦 Heritage Archive 파이프라인"
    echo "입력: $ROOT/data/persons.json"
    echo ""

    [ "$skip_embed" = false ] && run_embed
    run_freq
    run_similarity
    [ "$skip_extract" = false ] && run_extract
    run_build

    echo ""
    log_done "파이프라인 완료!"
    echo "📂 결과: $ROOT/dist/heritage-archive.html"
}

main "$@"
