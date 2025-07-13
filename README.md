# Stock Data Processing System

## 🏗️ 새로운 프로젝트 구조

```
stock-kafka/
├── src/
│   ├── processors/               # 🆕 통합 데이터 처리 폴더
│   │   ├── stock_data_processor.py    # 메인 통합 프로세서
│   │   ├── batch_runner.py            # 레거시 배치 처리
│   │   ├── enhanced_batch_processor.py # 개선된 배치 처리
│   │   └── hybrid_batch_manager.py    # 하이브리드 매니저
│   ├── kis_api_client.py
│   ├── api/
│   ├── cache_manager.py
│   └── database.py
├── scripts/
└── data/
```

## 🚀 사용법

### 1. 통합 프로세서 (추천)
```bash
# 일일 배치 처리
python src/processors/stock_data_processor.py --mode daily

# 과거 데이터 30일 적재
python src/processors/stock_data_processor.py --mode historical --days 30

# 실시간 모니터링
python src/processors/stock_data_processor.py --mode realtime

# 신호 탐지
python src/processors/stock_data_processor.py --mode signals

# 시스템 유지보수
python src/processors/stock_data_processor.py --mode maintenance
```

### 2. 개별 프로세서
```bash
# 개선된 배치 처리
python src/processors/enhanced_batch_processor.py

# 레거시 배치 처리
python src/processors/batch_runner.py
```

## 📊 처리 모드별 특징

### Historical Mode (과거 데이터)
- **목적**: 과거 데이터 대량 적재
- **특징**: python-kis 라이브러리의 while 루프 + 페이지네이션 활용
- **속도**: 최적화된 대량 처리 (15 req/sec)
- **대상**: 전체 종목 (Tier별 우선순위 적용)

### Realtime Mode (실시간)
- **목적**: 현재가 실시간 모니터링
- **특징**: 경량화된 빠른 신호 탐지
- **주기**: 5분마다 갱신
- **대상**: Tier 1 종목만 (AAPL, MSFT, GOOGL, AMZN, TSLA)

### Daily Mode (일일 배치)
- **목적**: 일일 종합 분석 및 신호 생성
- **특징**: 기술적 분석 + 신호 탐지 + DB 저장
- **주기**: 하루 1회 (미국 장 마감 후)
- **대상**: 전체 종목

### Signals Mode (신호 탐지)
- **목적**: 빠른 매매 신호 탐지
- **특징**: 캐시 기반 고속 처리
- **주기**: 실시간 (필요시)
- **알고리즘**: RSI < 30 (매수), RSI > 70 (매도)

## 🎯 주요 개선사항

### 1. 프로젝트 구조 통합
- ✅ 분산된 배치 프로세서들을 `src/processors/`로 통합
- ✅ 빈 폴더들 제거 (realtime_processor, signal_detector, dashboard)
- ✅ 명확한 책임 분리

### 2. 처리 효율성 향상
- ✅ python-kis 라이브러리 최적 활용 방식 적용
- ✅ Tier별 종목 관리 (우선순위 기반)
- ✅ 스마트 레이트 리미팅 (15 req/sec)
- ✅ 병렬 처리 및 캐시 활용

### 3. 운영 편의성
- ✅ CLI 인터페이스로 모드별 실행
- ✅ 실시간 로깅 및 상태 모니터링
- ✅ 에러 핸들링 및 복구 로직
- ✅ 유지보수 모드 추가

## 🔄 데이터 플로우

```
1. Historical Mode → DuckDB 대량 적재
2. Daily Mode → 기술적 분석 → 신호 생성 → 결과 저장
3. Realtime Mode → 현재가 모니터링 → 즉시 알림
4. Signals Mode → 캐시 기반 빠른 신호 → 실시간 알림
5. Maintenance Mode → 데이터 정리 → 시스템 최적화
```

## 📈 성능 벤치마크 (예상)

| 모드 | 종목수 | 처리 속도 | 메모리 사용량 | API 호출 |
|------|--------|-----------|---------------|----------|
| Historical | 15개 | 30일 → 15분 | ~500MB | 최적화됨 |
| Realtime | 5개 | 5분 주기 | ~50MB | 경량화됨 |
| Daily | 15개 | 10분 | ~200MB | 균형적 |
| Signals | 15개 | 1분 | ~30MB | 캐시 활용 |

## 🛠️ 다음 단계

1. **import 경로 수정**: 이동된 파일들의 import 문 업데이트
2. **테스트 실행**: 각 모드별 정상 동작 확인
3. **설정 파일**: 종목 리스트 및 파라미터 외부화
4. **모니터링**: 대시보드 및 알림 시스템 구축
5. **문서화**: API 문서 및 운영 가이드 작성

---

**이제 깔끔하게 정리된 프로젝트 구조에서 효율적인 데이터 처리가 가능합니다! 🎉**
