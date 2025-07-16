#!/bin/bash

# 폴더 구조 요약 스크립트
# Stock Kafka Pipeline 프로젝트용 간편 실행 스크립트

# 스크립트 경로 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 기본 설정
DEFAULT_DEPTH=3
DEFAULT_PATH="$PROJECT_ROOT"

# 도움말 표시
show_help() {
    echo "🗂️ 폴더 구조 요약 도구"
    echo "========================"
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  -d, --depth <숫자>    최대 탐색 깊이 (기본값: $DEFAULT_DEPTH)"
    echo "  -p, --path <경로>     탐색할 경로 (기본값: 현재 프로젝트 루트)"
    echo "  -o, --output <파일>   결과를 파일로 저장"
    echo "  -h, --help           이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  $0                    # 기본 설정으로 실행"
    echo "  $0 -d 2               # 깊이 2로 실행"
    echo "  $0 -o structure.txt   # 결과를 파일로 저장"
    echo ""
}

# 인자 파싱
DEPTH=$DEFAULT_DEPTH
PATH_ARG=$DEFAULT_PATH
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--depth)
            DEPTH="$2"
            shift 2
            ;;
        -p|--path)
            PATH_ARG="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "❌ 알 수 없는 옵션: $1"
            show_help
            exit 1
            ;;
    esac
done

# Python 환경 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3가 설치되지 않았습니다."
    exit 1
fi

# 스크립트 실행
echo "🚀 폴더 구조 요약 시작..."
echo "   - 탐색 깊이: $DEPTH"
echo "   - 탐색 경로: $PATH_ARG"
echo "   - 출력 파일: ${OUTPUT_FILE:-'화면 출력'}"
echo ""

# Python 스크립트 실행
if [[ -n "$OUTPUT_FILE" ]]; then
    python3 "$PROJECT_ROOT/src/folder_structure_summary.py" \
        --max-depth "$DEPTH" \
        --path "$PATH_ARG" \
        --output "$OUTPUT_FILE"
else
    python3 "$PROJECT_ROOT/src/folder_structure_summary.py" \
        --max-depth "$DEPTH" \
        --path "$PATH_ARG"
fi

echo "✅ 완료!"