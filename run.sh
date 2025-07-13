#!/bin/bash

# Stock Kafka Pipeline 실행 가이드 스크립트
# 프로젝트의 각 컴포넌트를 쉽게 실행할 수 있는 헬퍼 스크립트

set -e

PROJECT_ROOT=$(dirname "$(realpath "$0")")
cd "$PROJECT_ROOT"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 헬프 함수
show_help() {
    echo -e "${CYAN}📊 Stock Kafka Pipeline - 실행 가이드${NC}"
    echo -e "${YELLOW}사용법: ./run.sh [COMMAND] [OPTIONS]${NC}"
    echo ""
    echo -e "${GREEN}🚀 메인 프로그램:${NC}"
    echo "  daily         - 일일 배치 처리 (권장)"
    echo "  historical    - 과거 데이터 적재 (--days N)"
    echo "  realtime      - 실시간 모니터링"
    echo "  signals       - 신호 탐지"
    echo "  maintenance   - 시스템 유지보수"
    echo ""
    echo -e "${BLUE}🔄 레거시 프로그램:${NC}"
    echo "  legacy        - 기존 batch_runner.py 실행"
    echo ""
    echo -e "${PURPLE}🐳 인프라 관리:${NC}"
    echo "  setup         - Docker 인프라 시작"
    echo "  stop          - Docker 인프라 중지"
    echo "  status        - 시스템 상태 확인"
    echo ""
    echo -e "${CYAN}📊 대시보드 & 스트리밍:${NC}"
    echo "  dashboard     - Streamlit 대시보드 (구현 예정)"
    echo "  stream        - Kafka 스트림 처리 (구현 예정)"
    echo ""
    echo -e "${YELLOW}예시:${NC}"
    echo "  ./run.sh daily                    # 일일 배치 처리"
    echo "  ./run.sh historical --days 30     # 30일 과거 데이터"
    echo "  ./run.sh realtime                 # 실시간 모니터링"
    echo "  ./run.sh setup                    # 인프라 시작"
}

# Python 가상환경 활성화
activate_venv() {
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        echo -e "${GREEN}✅ Python 가상환경 활성화됨${NC}"
    else
        echo -e "${RED}❌ 가상환경이 없습니다. 먼저 설정하세요: python -m venv .venv${NC}"
        exit 1
    fi
}

# Docker 상태 확인
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker가 설치되지 않았습니다.${NC}"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose가 설치되지 않았습니다.${NC}"
        exit 1
    fi
}

# 메인 프로세서 실행
run_processor() {
    local mode=$1
    shift
    
    echo -e "${CYAN}🚀 Stock Data Processor 시작 - 모드: ${mode}${NC}"
    activate_venv
    
    if [ "$mode" = "historical" ] && [ "$1" = "--days" ]; then
        python src/processors/stock_data_processor.py --mode historical --days "$2"
    else
        python src/processors/stock_data_processor.py --mode "$mode" "$@"
    fi
}

# 레거시 배치 실행
run_legacy() {
    echo -e "${BLUE}🔄 레거시 배치 프로세서 시작${NC}"
    activate_venv
    python src/processors/batch_runner.py
}

# Docker 인프라 시작
setup_infrastructure() {
    echo -e "${PURPLE}🐳 Docker 인프라 시작 중...${NC}"
    check_docker
    
    docker compose up -d
    
    echo -e "${GREEN}✅ 인프라 시작 완료${NC}"
    echo -e "${YELLOW}📊 접속 정보:${NC}"
    echo "  - Kafka: localhost:9092"
    echo "  - Redis: localhost:6379"
    echo "  - DuckDB: data/duckdb/stock_data.db"
}

# Docker 인프라 중지
stop_infrastructure() {
    echo -e "${PURPLE}🛑 Docker 인프라 중지 중...${NC}"
    check_docker
    docker compose down
    echo -e "${GREEN}✅ 인프라 중지 완료${NC}"
}

# 시스템 상태 확인
check_status() {
    echo -e "${CYAN}📊 시스템 상태 확인${NC}"
    echo ""
    
    echo -e "${YELLOW}🐳 Docker 컨테이너:${NC}"
    if command -v docker &> /dev/null; then
        docker compose ps
    else
        echo "Docker가 설치되지 않음"
    fi
    
    echo ""
    echo -e "${YELLOW}🐍 Python 환경:${NC}"
    if [ -f ".venv/bin/python" ]; then
        .venv/bin/python --version
        echo "가상환경: 활성화됨"
    else
        echo "가상환경: 없음"
    fi
    
    echo ""
    echo -e "${YELLOW}📁 프로젝트 파일:${NC}"
    echo "프로세서: $(ls -1 src/processors/*.py | wc -l)개"
    echo "설정파일: $(ls -1 config/*.py 2>/dev/null | wc -l)개"
    echo "전체 Python 파일: $(find . -name "*.py" | grep -v .venv | wc -l)개"
}

# 대시보드 실행 (구현 예정)
run_dashboard() {
    echo -e "${CYAN}📊 Streamlit 대시보드 시작 (구현 예정)${NC}"
    echo -e "${YELLOW}⚠️  대시보드는 아직 구현되지 않았습니다.${NC}"
    echo -e "${BLUE}구현 위치: src/dashboard/main_dashboard.py${NC}"
    echo ""
    echo -e "${GREEN}구현 후 실행 명령:${NC}"
    echo "streamlit run src/dashboard/main_dashboard.py"
}

# 스트림 처리 실행 (구현 예정)
run_stream() {
    echo -e "${CYAN}🌊 Kafka 스트림 처리 시작 (구현 예정)${NC}"
    echo -e "${YELLOW}⚠️  스트림 처리는 아직 구현되지 않았습니다.${NC}"
    echo -e "${BLUE}구현 위치: src/streaming/${NC}"
    echo ""
    echo -e "${GREEN}구현 후 실행 명령:${NC}"
    echo "python src/streaming/kafka_producer.py"
    echo "python src/streaming/kafka_consumer.py"
}

# 메인 스위치
case "$1" in
    "daily")
        run_processor "daily" "${@:2}"
        ;;
    "historical")
        run_processor "historical" "${@:2}"
        ;;
    "realtime")
        run_processor "realtime" "${@:2}"
        ;;
    "signals")
        run_processor "signals" "${@:2}"
        ;;
    "maintenance")
        run_processor "maintenance" "${@:2}"
        ;;
    "legacy")
        run_legacy
        ;;
    "setup")
        setup_infrastructure
        ;;
    "stop")
        stop_infrastructure
        ;;
    "status")
        check_status
        ;;
    "dashboard")
        run_dashboard
        ;;
    "stream")
        run_stream
        ;;
    "help"|"-h"|"--help"|"")
        show_help
        ;;
    *)
        echo -e "${RED}❌ 알 수 없는 명령: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
