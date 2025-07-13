# 한국투자증권 OpenAPI 설정 가이드

## 📋 필수 준비사항

### 1. 한국투자증권 계좌 개설
- 한국투자증권에서 주식 계좌를 개설해야 합니다
- 모의투자 계좌도 가능합니다

### 2. OpenAPI 서비스 신청

#### 단계 1: 한국투자증권 OpenAPI 포털 접속
- 웹사이트: https://apiportal.koreainvestment.com/
- 한국투자증권 홈페이지에서도 접근 가능

#### 단계 2: 회원가입/로그인
- 한국투자증권 계좌 정보로 로그인
- 또는 새로 회원가입

#### 단계 3: API 서비스 신청
1. **"API 서비스 신청"** 클릭
2. **신청서 작성**:
   - 개인/법인 정보 입력
   - 사용 목적: "개인 투자 분석 및 자동화"
   - 개발 언어: "Python"
   - 개발 목적: "NASDAQ 주식 분석 및 매매 신호 탐지"

3. **서비스 선택**:
   - ✅ 국내주식 시세조회
   - ✅ 해외주식 시세조회 (중요!)
   - ✅ 국내주식 주문
   - ✅ 해외주식 주문

#### 단계 4: 승인 대기
- 승인까지 1-3일 소요
- 승인 후 이메일 또는 SMS 알림

### 3. API 키 발급

승인 후 API 포털에서 확인 가능:

#### APP KEY & APP SECRET 확인
1. API 포털 로그인
2. "내 애플리케이션" 메뉴 클릭
3. 생성된 애플리케이션 클릭
4. **APP KEY**와 **APP SECRET** 복사

## 🔑 .env 파일 설정

```bash
# 발급받은 값으로 수정하세요
KIS_APP_KEY=PABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890
KIS_APP_SECRET=abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyz1234567890
KIS_ACCESS_TOKEN=
```

## 📝 설정 확인

```bash
# 가상환경 활성화
uv venv

# 테스트 실행
uv run python src/test_api.py
```

## 🚨 중요 사항

### 1. 모의투자 vs 실제투자
- 개발 초기에는 **모의투자**로 테스트 권장
- `.env` 파일의 `KIS_PAPER_TRADING=true` 설정 유지

### 2. API 호출 제한
- **초당 20회**
- **분당 1,000회**  
- **시간당 10,000회**

### 3. 보안 주의사항
- API 키는 절대 공개하지 마세요
- `.env` 파일을 Git에 커밋하지 마세요
- 정기적으로 API 키를 갱신하세요

### 4. 해외주식 거래 시간 (미국 동부시간)
- **정규장**: 09:30 ~ 16:00
- **프리마켓**: 04:00 ~ 09:30  
- **애프터마켓**: 16:00 ~ 20:00

## 🔍 문제 해결

### API 키 발급이 안 되는 경우
1. 한국투자증권 계좌 상태 확인
2. 신청서 정보 재확인
3. 고객센터 문의 (1588-0800)

### 토큰 발급 오류
- APP_KEY와 APP_SECRET 재확인
- 네트워크 연결 상태 확인
- API 서버 상태 확인

## 📞 고객 지원

- **한국투자증권 고객센터**: 1588-0800
- **OpenAPI 문의**: https://apiportal.koreainvestment.com/
- **개발자 가이드**: API 포털 내 문서 참고

---

✅ API 키 발급 완료 후 `uv run python src/test_api.py`로 테스트해보세요!
