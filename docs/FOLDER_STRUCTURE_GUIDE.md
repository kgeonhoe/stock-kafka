# 폴더 구조 요약 도구 사용법

## 개요
`folder_structure_summary.py`는 Stock Kafka Pipeline 프로젝트의 폴더 구조를 시각적으로 요약해주는 유틸리티입니다.

## 주요 기능
- 📁 트리 형태의 폴더 구조 표시
- 🏷️ 각 폴더와 파일에 대한 한국어 설명
- 📊 프로젝트 통계 정보 제공
- 🎯 탐색 깊이 조절 가능
- 💾 결과 파일 저장 지원

## 사용 방법

### 1. Python 스크립트 직접 실행
```bash
# 기본 실행 (깊이 3)
python src/folder_structure_summary.py

# 깊이 조절
python src/folder_structure_summary.py --max-depth 2

# 다른 경로 탐색
python src/folder_structure_summary.py --path /path/to/directory

# 결과 파일로 저장
python src/folder_structure_summary.py --output structure.txt
```

### 2. 쉘 스크립트 실행 (권장)
```bash
# 기본 실행
./scripts/folder_summary.sh

# 깊이 조절
./scripts/folder_summary.sh -d 2

# 결과 파일로 저장
./scripts/folder_summary.sh -d 3 -o project_structure.txt

# 도움말 확인
./scripts/folder_summary.sh --help
```

## 출력 예시
```
📁 Stock Kafka Pipeline - 폴더 구조 요약
==================================================
프로젝트 경로: /home/runner/work/stock-kafka/stock-kafka
최대 탐색 깊이: 2
생성 시간: Wed Jul 16 23:37:48 UTC 2025

🗂️ 디렉토리 구조:
└── stock-kafka - 📁 프로젝트 루트 디렉토리
    ├── config - ⚙️ 설정 파일 - 시스템 구성
    │   ├── database_config.py
    │   ├── kafka_config.py
    │   └── kis_config.py
    ├── data - 📊 데이터 저장소 - 데이터베이스 및 캐시
    │   └── duckdb - 🦆 DuckDB 데이터베이스 파일
    │       └── stock_data.db
    ├── src - 🏗️ 소스 코드 - 메인 애플리케이션 로직
    │   ├── processors - ⚙️ 데이터 처리기 - 배치 및 실시간 처리
    │   │   ├── batch_runner.py
    │   │   └── stock_data_processor.py
    │   └── folder_structure_summary.py
    └── README.md - 📖 프로젝트 소개 및 사용법

==================================================
📊 요약 통계:
- 총 탐색된 아이템: 36
- 디렉토리 수: 9
- 파일 수: 27
```

## 명령어 옵션

### Python 스크립트 옵션
| 옵션 | 짧은 형태 | 설명 | 기본값 |
|------|-----------|------|--------|
| `--path` | `-p` | 탐색할 디렉토리 경로 | `.` (현재 디렉토리) |
| `--max-depth` | `-d` | 최대 탐색 깊이 | `3` |
| `--output` | `-o` | 결과를 저장할 파일 경로 | 화면 출력 |

### 쉘 스크립트 옵션
| 옵션 | 짧은 형태 | 설명 | 기본값 |
|------|-----------|------|--------|
| `--depth` | `-d` | 최대 탐색 깊이 | `3` |
| `--path` | `-p` | 탐색할 디렉토리 경로 | 프로젝트 루트 |
| `--output` | `-o` | 결과를 저장할 파일 경로 | 화면 출력 |
| `--help` | `-h` | 도움말 표시 | - |

## 특징

### 지원하는 설명
- **디렉토리**: 각 폴더의 역할과 목적을 한국어로 설명
- **파일**: 주요 설정 파일들의 용도 설명
- **아이콘**: 폴더와 파일 타입별 직관적인 아이콘 표시

### 자동 필터링
다음 파일/폴더들은 자동으로 제외됩니다:
- `.git`, `__pycache__`, `.pytest_cache`
- `node_modules`, `.venv`, `venv`
- `.mypy_cache`, `.tox`, `.coverage`
- IDE 관련 폴더 (`.idea`, `.vscode`)
- 빌드 아티팩트 (`dist`, `build`, `*.egg-info`)

### 통계 정보
- 총 탐색된 아이템 수
- 디렉토리 개수
- 파일 개수

## 활용 예시

### 1. 프로젝트 구조 문서화
```bash
# 프로젝트 구조를 문서로 저장
./scripts/folder_summary.sh -d 4 -o docs/PROJECT_STRUCTURE.md
```

### 2. 새로운 팀원 온보딩
```bash
# 간단한 구조 설명용
./scripts/folder_summary.sh -d 2
```

### 3. 코드 리뷰 시 참고
```bash
# 전체 구조를 파일로 저장하여 공유
./scripts/folder_summary.sh -o structure_review.txt
```

## 확장 가능성

이 도구는 다음과 같이 확장할 수 있습니다:
- 파일 크기 정보 추가
- 최근 수정 시간 표시
- 코드 라인 수 통계
- 언어별 파일 분류
- 의존성 분석 결과 통합

## 문의사항

도구 사용 중 문제가 발생하거나 개선 사항이 있으시면 이슈를 등록해주세요.