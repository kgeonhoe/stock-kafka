# 📊 Stock Kafka Pipeline - 프로젝트 아키텍처

## 🏗️ **전체 시스템 구조**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Stock Data Pipeline                          │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│   Data Source   │   Processing    │     Storage     │  Output   │
├─────────────────┼─────────────────┼─────────────────┼───────────┤
│                 │                 │                 │           │
│  KIS API        │  Batch Runner   │    DuckDB       │ Dashboard │
│  (한국투자증권)    │  (일일 분석)     │   (시계열 DB)    │(Streamlit)│
│                 │                 │                 │           │
│  Real-time      │  Signal Detect  │     Redis       │  Alerts   │
│  (실시간 가격)     │  (신호 탐지)     │    (캐시)       │ (알림)     │
│                 │                 │                 │           │
│  Historical     │  Maintenance    │     Kafka       │  Stream   │
│  (과거 데이터)     │  (시스템 관리)   │   (메시지큐)     │ (실시간)   │
└─────────────────┴─────────────────┴─────────────────┴───────────┘
```

---

## 🚀 **실행 프로그램 가이드**

### **1. 시스템 인프라 시작**

```bash
# Docker 컨테이너 시작 (Kafka, Redis, DuckDB)
docker-compose up -d

# 상태 확인
docker-compose ps
```

### **2. 메인 데이터 처리 프로그램**

#### **📊 통합 데이터 프로세서** (핵심 프로그램)
```bash
# 🔧 위치: src/processors/stock_data_processor.py

# 일일 배치 처리 (매일 실행 권장)
.venv/bin/python src/processors/stock_data_processor.py --mode daily

# 과거 데이터 초기 적재 (최초 1회)
.venv/bin/python src/processors/stock_data_processor.py --mode historical --days 90

# 실시간 모니터링 (장중 실행)
.venv/bin/python src/processors/stock_data_processor.py --mode realtime

# 신호 탐지 (수시 실행)
.venv/bin/python src/processors/stock_data_processor.py --mode signals

# 시스템 유지보수 (주 1회)
.venv/bin/python src/processors/stock_data_processor.py --mode maintenance
```

#### **🔄 레거시 배치 프로세서** (기존 로직)
```bash
# 🔧 위치: src/processors/batch_runner.py
# 전체 분석 파이프라인 (기존 방식)
.venv/bin/python src/processors/batch_runner.py
```

### **3. 스트리밍 및 대시보드**

#### **📈 Streamlit 대시보드** (예정)
```bash
# 🔧 위치: src/dashboard/ (구현 예정)
streamlit run src/dashboard/main_dashboard.py

# 접속: http://localhost:8501
```

#### **🌊 Kafka 스트림 처리** (예정)
```bash
# 🔧 위치: src/streaming/ (구현 예정)
.venv/bin/python src/streaming/kafka_consumer.py
.venv/bin/python src/streaming/kafka_producer.py
```

---

## 📁 **상세 디렉토리 구조**

```
stock-kafka/
├── 🚀 src/processors/              # 메인 실행 프로그램들
│   ├── stock_data_processor.py     # ⭐ 통합 프로세서 (5가지 모드)
│   └── batch_runner.py            # 🔄 레거시 배치 프로세서
│
├── 🏦 src/                        # 핵심 라이브러리
│   ├── kis_api_client.py          # KIS API 클라이언트
│   ├── cache_manager.py           # Redis 캐시 관리
│   ├── database.py               # DuckDB 데이터베이스
│   ├── technical_analysis.py     # 기술적 분석 엔진
│   └── api/bulk_data_client.py   # 대량 데이터 처리
│
├── 📊 src/dashboard/              # 웹 대시보드 (구현 예정)
│   ├── main_dashboard.py         # Streamlit 메인 대시보드
│   ├── pages/                    # 대시보드 페이지들
│   └── components/               # UI 컴포넌트들
│
├── 🌊 src/streaming/              # 실시간 스트리밍 (구현 예정)
│   ├── kafka_producer.py         # Kafka 프로듀서
│   ├── kafka_consumer.py         # Kafka 컨슈머
│   └── stream_processor.py       # 스트림 처리 로직
│
├── ⚙️ config/                     # 설정 파일들
│   ├── kis_config.py             # KIS API 설정
│   └── kafka_config.py           # Kafka 설정
│
├── 🗄️ data/                      # 데이터 저장소
│   ├── duckdb/                   # DuckDB 파일들
│   ├── cache/                    # 캐시 데이터
│   └── exports/                  # 내보내기 파일들
│
└── 🐳 Infrastructure
    ├── docker-compose.yml        # 도커 컨테이너 설정
    ├── Dockerfile               # 애플리케이션 이미지
    └── scripts/setup.sh         # 초기 설정 스크립트
```

---

## ⚡ **운영 시나리오별 실행 가이드**

### **🌅 일일 운영 (Daily Operations)**
```bash
# 1. 시스템 시작
docker-compose up -d

# 2. 일일 데이터 수집 및 분석
.venv/bin/python src/processors/stock_data_processor.py --mode daily

# 3. 대시보드 확인
streamlit run src/dashboard/main_dashboard.py
```

### **🔄 실시간 모니터링 (Live Monitoring)**
```bash
# 터미널 1: 실시간 데이터 처리
.venv/bin/python src/processors/stock_data_processor.py --mode realtime

# 터미널 2: 신호 탐지
.venv/bin/python src/processors/stock_data_processor.py --mode signals

# 터미널 3: 대시보드
streamlit run src/dashboard/main_dashboard.py
```

### **📚 초기 데이터 구축 (Initial Setup)**
```bash
# 1. 인프라 시작
docker-compose up -d

# 2. 90일 과거 데이터 적재
.venv/bin/python src/processors/stock_data_processor.py --mode historical --days 90

# 3. 초기 분석 실행
.venv/bin/python src/processors/stock_data_processor.py --mode daily
```

### **🧹 주간 유지보수 (Weekly Maintenance)**
```bash
# 시스템 정리 및 최적화
.venv/bin/python src/processors/stock_data_processor.py --mode maintenance
```

---

## 🌊 **데이터 플로우 (Data Flow)**

```
1. 📥 Data Ingestion
   KIS API → stock_data_processor.py → DuckDB/Redis

2. 🔄 Processing Pipeline  
   Raw Data → Technical Analysis → Signal Detection → Storage

3. 📊 Analytics & Visualization
   DuckDB → Streamlit Dashboard → Real-time Charts

4. 🚨 Real-time Alerts
   Signal Detection → Kafka → Notification System

5. 📈 Stream Processing
   Kafka → Stream Processor → Live Updates
```

---

## 🎯 **핵심 실행 포인트**

### **메인 프로그램**
- **`stock_data_processor.py`** - 모든 데이터 처리의 중심
- **5가지 모드**로 다양한 상황에 대응

### **스트리밍**
- **Kafka** - 실시간 메시지 큐
- **Streamlit** - 웹 대시보드
- **Redis** - 빠른 캐시 및 알림

### **자동화**
- **Docker Compose** - 원클릭 인프라 시작
- **CLI 인터페이스** - 쉬운 모드 전환
- **스케줄링** - cron job으로 자동 실행

---

**🎉 이제 목적에 맞는 프로그램을 선택해서 실행하세요!**
