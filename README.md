# 🐦 조류 충돌 통합 모니터링 시스템

전국 조류 유리창 충돌 사고 데이터를 실시간으로 분석하고 모니터링하는 종합 시스템입니다.

## 📊 시스템 개요

이 시스템은 2023-2024년 전국 조류 충돌 사고 데이터(15,118건)를 바탕으로 다음과 같은 기능을 제공합니다:

- **실시간 모니터링**: 사고 발생 패턴과 위험도 추적
- **데이터 시각화**: 인터랙티브 차트, 지도, 대시보드
- **정책 권고**: 과학적 근거 기반 조류 보호 정책 제안
- **알림 시스템**: 고위험 상황 발생 시 자동 알림
- **종합 분석**: 시설물별, 종별, 지역별 상세 분석

## 🗂️ 주요 구성 요소

### 1. 데이터 분석 스크립트
- `correct_bird_analysis.py` - 기본 데이터 분석 및 통계
- `advanced_statistical_analysis.py` - 고급 통계 분석 및 위험도 평가
- `policy_guidelines_generator.py` - 정책 권고사항 생성

### 2. 웹 인터페이스
- `real_time_monitoring_dashboard.html` - 실시간 모니터링 대시보드
- `bird_collision_dashboard.html` - 데이터 탐색 대시보드
- `bird_collision_map.html` - 인터랙티브 지도 뷰어
- `policy_recommendations.html` - 정책 문서 뷰어

### 3. 모니터링 시스템
- `integrated_monitoring_system.py` - 통합 모니터링 시스템
- `notification_system.py` - 알림 및 경고 시스템
- `system_integration.py` - 전체 시스템 통합 관리

## 🚀 시작하기

### 1. 전체 시스템 실행
```bash
python system_integration.py --start
```

### 2. 개별 컴포넌트 실행

#### 데이터 분석
```bash
python correct_bird_analysis.py
python advanced_statistical_analysis.py
python policy_guidelines_generator.py
```

#### 모니터링 시스템
```bash
python integrated_monitoring_system.py
```

#### 웹 서버 (수동)
```bash
python -m http.server 8000
```

### 3. 대시보드 접속
웹 서버 실행 후 브라우저에서 접속:
- 실시간 모니터링: http://localhost:8000/real_time_monitoring_dashboard.html
- 데이터 대시보드: http://localhost:8000/bird_collision_dashboard.html
- 지도 뷰어: http://localhost:8000/bird_collision_map.html
- 정책 문서: http://localhost:8000/policy_recommendations.html

## 📈 주요 분석 결과

### 시설물별 사고 현황
- **방음벽**: 11,479건 (75.9%) - 최대 위험 시설
- **건물**: 2,624건 (17.4%) - 중간 위험
- **기타**: 1,015건 (6.7%) - 낮은 위험

### 고위험 조류 종
1. **멧비둘기**: 2,149건 (위험도 점수: 2,324)
2. **직박구리**: 834건 (위험도 점수: 1,019)
3. **참새**: 681건 (위험도 점수: 866)
4. **물까치**: 511건 (위험도 점수: 656)
5. **박새**: 380건 (위험도 점수: 565)

### 지역별 위험도
- **고위험 지역**: 광주, 전북, 전남
- **중위험 지역**: 경기, 서울, 부산
- **모니터링 범위**: 전국 17개 시도

## 🛠️ 시스템 기능

### 실시간 모니터링
- 일일 사고 건수 추적
- 위험도 수준별 자동 분류
- 지역별 사고 패턴 분석
- 예측 알고리즘 기반 위험지역 식별

### 알림 시스템
- **Critical (긴급)**: 일일 10건 이상 발생 시
- **High (주의)**: 일일 5-9건 발생 시
- **Medium (관심)**: 일일 2-4건 발생 시
- **Low (정상)**: 일일 1건 발생 시

### 권장 조치사항
#### 긴급 대응 (Critical)
- 즉시 현장 조사팀 파견
- 임시 방음벽 설치 또는 보완
- 조류 유도 장치 긴급 설치
- 연속 3일간 집중 모니터링

#### 예방 조치 (High)
- 24시간 내 현장 점검
- 조류 회피 장치 점검 및 보완
- 주변 환경 요인 조사

## 📋 정책 권고사항

### 1. 법적 프레임워크
- 조류 보호법 개정안 제안
- 건축법 시행령 개정 (조류 친화적 설계 의무화)
- 환경영향평가 기준 강화

### 2. 기술적 가이드라인
- 유리창 투명도 제한 (가시광선 투과율 70% 이하)
- 버드세이버 설치 의무화 (고위험 지역)
- 조류 친화적 건축 설계 인증 시스템

### 3. 관리 전략
- 3단계 위험도 관리 시스템
- 지역별 전담 관리기관 지정
- 시민 참여형 모니터링 네트워크

### 4. 예산 및 일정
- **총 예산**: 2,500억원 (5년간)
- **1단계** (1년): 법적 기반 구축 (500억원)
- **2단계** (2-3년): 시설 보강 및 시스템 구축 (1,500억원)
- **3단계** (4-5년): 운영 및 확산 (500억원)

## 📊 데이터 파일

### 입력 데이터
- `조류유리창_충돌사고_2023_2024_전국.gpkg` - 원본 GeoPackage 데이터

### 분석 결과 파일
- `bird_analysis_results.json` - 기본 분석 결과
- `advanced_analysis_data.json` - 고급 분석 결과
- `comprehensive_policy_document.json` - 정책 권고사항
- `monitoring_report.json` - 실시간 모니터링 보고서

### 시각화 데이터
- `bird_collision_data.geojson` - 지도 시각화용 GeoJSON
- 다양한 차트 및 그래프 데이터

## 🔧 기술 스택

### Backend
- **Python 3.x**
- **SQLite/GeoPackage** - 공간 데이터베이스
- **Pandas** - 데이터 분석
- **JSON** - 데이터 교환

### Frontend
- **HTML5/CSS3/JavaScript**
- **Leaflet.js** - 인터랙티브 지도
- **Chart.js** - 데이터 시각화
- **Bootstrap** - 반응형 UI

### 시스템 통합
- **HTTP Server** - 웹 서비스
- **Threading** - 백그라운드 모니터링
- **Logging** - 시스템 로깅

## 🎯 향후 계획

### 단기 (3개월)
- [ ] 실시간 데이터 수집 API 구축
- [ ] 모바일 앱 개발
- [ ] 머신러닝 예측 모델 고도화

### 중기 (6개월)
- [ ] 전국 센서 네트워크 구축
- [ ] 정부기관 연계 시스템
- [ ] 국제 조류 보호 네트워크 참여

### 장기 (1년)
- [ ] AI 기반 자동 대응 시스템
- [ ] 스마트시티 통합 솔루션
- [ ] 글로벌 표준 모델 제시

## 🤝 기여하기

이 프로젝트는 조류 보호와 도시 생태계 개선을 위한 오픈소스 프로젝트입니다. 
기여를 원하시는 분은 다음 영역에서 도움을 주실 수 있습니다:

- 데이터 수집 및 검증
- 알고리즘 개선
- UI/UX 개선
- 문서화
- 정책 제안

## 📞 연락처

조류 보호 및 모니터링 시스템 관련 문의:
- 이메일: bird.monitoring@example.com
- 이슈 트래킹: GitHub Issues
- 문서: 프로젝트 Wiki

---

**© 2024 조류 충돌 통합 모니터링 시스템. 모든 권리 보유.**