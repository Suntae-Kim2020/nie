# ChatGPT Desktop MCP 설정 가이드
## 조류충돌 SQLite 데이터베이스 연결

### 1. ChatGPT Desktop 설정

1. **ChatGPT Desktop 앱 열기**
2. **설정 메뉴 접근**:
   - macOS: ChatGPT → Preferences 또는 ⌘,
   - Windows: 설정 아이콘 클릭
3. **연결/통합 탭으로 이동**:
   - "Connections" 또는 "Integrations" 탭 선택

### 2. MCP 서버 연결 추가

**방법 1: Local HTTP MCP Server (가장 권장)**
- **연결 유형**: HTTP MCP Server
- **URL**: `http://127.0.0.1:8080`
- **Authentication**: Bearer Token
- **API Key**: `bird_collision_mcp_2024_secure_key_xyz789`
- **Status**: ✅ 활성화됨 (로컬 서버 실행 중)

**방법 2: Local Command Line MCP Server**
- **연결 유형**: Local/Command Line MCP Server
- **Name**: `Bird Collision SQLite Database`
- **Command**: `python3`
- **Arguments**: `/Users/suntaekim/nie/mcp_standard_server.py`
- **Working Directory**: `/Users/suntaekim/nie`
- **Environment Variables**: `DATABASE_PATH=/Users/suntaekim/nie/bird_collision_mcp.db`

**방법 3: 간단한 스크립트 실행 (대안)**
- **연결 유형**: Custom Script
- **Command**: `cd /Users/suntaekim/nie && export DATABASE_PATH="/Users/suntaekim/nie/bird_collision_mcp.db" && python3 mcp_standard_server.py`

**방법 4: HTTP 연결 via ngrok (외부 접근)**
- **URL**: `https://052dc2ff1152.ngrok-free.app`
- **Authentication**: Bearer Token
- **API Key**: `bird_collision_mcp_2024_secure_key_xyz789`
- **Status**: 활성화됨 (ngrok 무료 브라우저 warning 우회 필요)

### 3. 권한 설정
- ✅ 파일 시스템 읽기 권한
- ✅ 데이터베이스 접근 권한
- ✅ Python 스크립트 실행 권한

### 4. 연결 테스트

연결 후 ChatGPT에서 다음과 같이 테스트:

```
조류충돌 데이터베이스의 테이블 구조를 보여줘
```

또는

```
가장 많이 충돌하는 조류 종 TOP 5를 알려줘
```

### 5. 사용 가능한 쿼리 예시

#### 기본 통계
```sql
SELECT COUNT(*) as 총사고건수, 
       COUNT(DISTINCT korean_name) as 조류종수,
       COUNT(DISTINCT province) as 지역수
FROM bird_collisions;
```

#### 위험한 조류 종 TOP 10
```sql
SELECT korean_name, incident_count, total_individuals 
FROM species_statistics 
LIMIT 10;
```

#### 지역별 사고 현황
```sql
SELECT province, total_incidents, species_count 
FROM province_statistics 
ORDER BY total_incidents DESC;
```

#### 월별 트렌드
```sql
SELECT year, month, incidents, species_count 
FROM monthly_trends 
ORDER BY year, month;
```

#### 계절별 패턴
```sql
SELECT season, incidents, species_count 
FROM seasonal_analysis;
```

### 6. MCP HTTP 서버 시작 방법

**현재 상태**: ✅ 서버 실행 중 (백그라운드)

**서버 수동 시작**:
```bash
cd /Users/suntaekim/nie
export DATABASE_PATH="/Users/suntaekim/nie/bird_collision_mcp.db"
export MCP_API_KEY="bird_collision_mcp_2024_secure_key_xyz789"
python3 mcp_http_server.py
```

**서버 확인**:
- Health Check: `curl -H "Authorization: Bearer bird_collision_mcp_2024_secure_key_xyz789" http://127.0.0.1:8080/health`
- Tools List: `curl -H "Authorization: Bearer bird_collision_mcp_2024_secure_key_xyz789" http://127.0.0.1:8080/mcp/tools`

### 7. 문제 해결

**HTTP 연결 실패 시**:
1. 서버 실행 확인: `http://127.0.0.1:8080/health`
2. 인증 토큰 확인: `bird_collision_mcp_2024_secure_key_xyz789`
3. 포트 충돌 확인: `lsof -i :8080`

**로컬 실행 연결 실패 시**:
1. Python 경로 확인: `which python` 또는 `which python3`
2. 파일 권한 확인: `ls -la mcp_http_server.py`
3. 데이터베이스 파일 존재 확인: `ls -la bird_collision_mcp.db`

**쿼리 실행 오류 시**:
1. 테이블명/컬럼명 확인
2. SQL 문법 검증
3. 서버 로그 확인

### 8. 데이터베이스 정보

**주요 테이블**:
- `bird_collisions`: 조류충돌 원본 데이터
- `species_statistics`: 조류별 통계 (뷰)
- `province_statistics`: 지역별 통계 (뷰)
- `monthly_trends`: 월별 트렌드 (뷰)
- `facility_analysis`: 시설물별 분석 (뷰)
- `seasonal_analysis`: 계절별 분석 (뷰)

**데이터 기간**: 2023-2024년
**총 레코드**: 약 수만 건
**조류 종수**: 100+ 종
**지역**: 전국 17개 시도

이제 ChatGPT Desktop에서 조류충돌 데이터를 자유롭게 질의하고 분석할 수 있습니다!