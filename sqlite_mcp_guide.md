# 🐦 SQLite MCP 테스트 가이드

SQLite 데이터베이스를 통한 ChatGPT MCP 기능 테스트 완전 가이드입니다.

## 📋 준비된 파일들

### 데이터베이스
- **`bird_collision_mcp.db`** (2.21 MB)
  - 8,598개 조류 충돌 레코드
  - 129개 조류 종
  - 17개 시도 지역
  - 완전히 정규화된 데이터

### 쿼리 파일들
- `sqlite_mcp_queries.json` - 모든 쿼리 모음
- `sqlite_mcp_query_*.sql` - 개별 테스트 쿼리들
- `sqlite_mcp_test_results.json` - 연결 테스트 결과

## 🚀 MCP 서버 설정

### 1. Claude Desktop 설정

Claude Desktop의 설정 파일을 수정합니다:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "sqlite": {
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-sqlite",
        "/Users/suntaekim/nie/bird_collision_mcp.db"
      ]
    }
  }
}
```

### 2. MCP 서버 설치 (필요한 경우)

```bash
# SQLite MCP 서버 설치
npm install -g @modelcontextprotocol/server-sqlite

# 또는 npx로 바로 사용 (권장)
npx @modelcontextprotocol/server-sqlite --help
```

### 3. 데이터베이스 경로 확인

현재 데이터베이스 절대 경로:
```bash
pwd
# /Users/suntaekim/nie

ls -la bird_collision_mcp.db
# 파일 존재 확인
```

## 📊 데이터베이스 구조

### 메인 테이블: `bird_collisions`
```sql
-- 테이블 구조 확인
.schema bird_collisions
```

**주요 컬럼:**
- `id`: 기본 키
- `korean_name`: 조류 한글명
- `migratory_type`: 철새유형 (텃새/여름철새/겨울철새/나그네새)
- `facility_type`: 시설물유형 (방음벽/건물/기타)
- `province`: 시도명
- `observation_date`: 관찰일자
- `individual_count`: 개체수
- `latitude`, `longitude`: 위도, 경도
- `bird_saver`: 버드세이버 설치여부

### 통계 뷰들
- `species_statistics`: 종별 통계
- `province_statistics`: 지역별 통계  
- `monthly_trends`: 월별 추이
- `facility_analysis`: 시설물별 분석
- `seasonal_analysis`: 계절별 분석

## 🧪 ChatGPT MCP 테스트 질의들

### 1. 기본 통계 질의
```
"조류 충돌 데이터베이스의 기본 통계를 알려주세요"
"총 몇 건의 사고가 기록되어 있나요?"
"가장 많이 충돌하는 조류 종은 무엇인가요?"
```

### 2. 지역별 분석
```
"지역별 사고 발생 순위를 알려주세요"
"서울에서 가장 많이 발생하는 조류 충돌은?"
"각 지역별로 영향받은 조류 종 수는 몇 개인가요?"
```

### 3. 시설물별 분석
```
"시설물별 사고 비율을 분석해주세요"
"방음벽에서 발생하는 사고의 특징은?"
"버드세이버 설치 효과를 분석해주세요"
```

### 4. 시간적 패턴 분석
```
"월별 사고 추이를 보여주세요"
"계절별 조류 충돌 패턴은 어떻게 되나요?"
"2023년과 2024년 사고 비교 분석해주세요"
```

### 5. 조류 생태 분석
```
"텃새와 철새 중 어느 쪽이 더 많이 충돌하나요?"
"철새유형별 사고 특성을 분석해주세요"
"가장 위험한 조류 종 TOP 10을 알려주세요"
```

### 6. 지리적 분석
```
"위도/경도 기반으로 사고 핫스팟을 찾아주세요"
"지역별 평균 좌표와 사고 밀도를 분석해주세요"
"특정 지역의 사고 클러스터링을 수행해주세요"
```

## 📝 직접 SQL 실행 예시

ChatGPT에서 다음과 같은 SQL을 직접 실행할 수 있습니다:

### 기본 통계
```sql
SELECT 
    COUNT(*) as total_incidents,
    COUNT(DISTINCT korean_name) as species_count,
    COUNT(DISTINCT province) as province_count
FROM bird_collisions;
```

### 종별 위험도 순위
```sql
SELECT * FROM species_statistics LIMIT 10;
```

### 지역별 상세 분석
```sql
SELECT * FROM province_statistics;
```

### 시설물별 분석
```sql
SELECT * FROM facility_analysis;
```

### 월별 트렌드
```sql
SELECT 
    year || '-' || printf('%02d', month) as year_month,
    incidents,
    species_count
FROM monthly_trends
ORDER BY year, month;
```

### 계절별 패턴
```sql
SELECT * FROM seasonal_analysis;
```

### 버드세이버 효과
```sql
SELECT 
    bird_saver,
    COUNT(*) as incidents,
    COUNT(DISTINCT korean_name) as species_affected,
    AVG(individual_count) as avg_individuals
FROM bird_collisions
WHERE bird_saver IN ('Y', 'N')
GROUP BY bird_saver;
```

### 지리적 핫스팟
```sql
SELECT 
    province,
    korean_name,
    COUNT(*) as incidents,
    AVG(latitude) as avg_lat,
    AVG(longitude) as avg_lng
FROM bird_collisions
WHERE latitude IS NOT NULL
GROUP BY province, korean_name
HAVING incidents >= 10
ORDER BY incidents DESC;
```

## 🔍 고급 분석 예시

### 1. 복합 조건 분석
```sql
SELECT 
    province,
    facility_type,
    migratory_type,
    COUNT(*) as incidents,
    GROUP_CONCAT(DISTINCT korean_name) as species_list
FROM bird_collisions
GROUP BY province, facility_type, migratory_type
HAVING incidents >= 5
ORDER BY incidents DESC;
```

### 2. 시계열 분석
```sql
SELECT 
    strftime('%Y-%m', observation_date) as month,
    facility_type,
    COUNT(*) as incidents
FROM bird_collisions
WHERE observation_date IS NOT NULL
GROUP BY strftime('%Y-%m', observation_date), facility_type
ORDER BY month, facility_type;
```

### 3. 상관관계 분석
```sql
SELECT 
    migratory_type,
    facility_type,
    COUNT(*) as incidents,
    AVG(individual_count) as avg_individuals,
    COUNT(DISTINCT province) as provinces_affected
FROM bird_collisions
WHERE migratory_type IS NOT NULL
GROUP BY migratory_type, facility_type
ORDER BY incidents DESC;
```

## 🛠️ 트러블슈팅

### MCP 연결 문제
1. **Claude Desktop 재시작** 필요
2. **설정 파일 경로** 확인
3. **데이터베이스 파일 경로** 절대경로로 수정

### 데이터베이스 문제
```bash
# SQLite 직접 연결 테스트
sqlite3 bird_collision_mcp.db

# 테이블 확인
.tables

# 샘플 데이터 확인
SELECT * FROM bird_collisions LIMIT 5;

# 종료
.quit
```

### 권한 문제
```bash
# 파일 권한 확인
ls -la bird_collision_mcp.db

# 권한 수정 (필요한 경우)
chmod 644 bird_collision_mcp.db
```

## 📈 성능 최적화

### 인덱스 확인
```sql
-- 생성된 인덱스 확인
.indices bird_collisions

-- 쿼리 실행 계획 확인
EXPLAIN QUERY PLAN 
SELECT * FROM bird_collisions 
WHERE korean_name = '멧비둘기';
```

### 통계 업데이트
```sql
-- SQLite 통계 업데이트
ANALYZE;
```

## 🎯 테스트 목표

1. **기본 쿼리**: SELECT, WHERE, GROUP BY, ORDER BY
2. **집계 함수**: COUNT, SUM, AVG, MIN, MAX
3. **조인**: 뷰를 통한 복합 데이터 조회
4. **시계열**: 날짜/시간 기반 분석
5. **문자열 처리**: LIKE, GROUP_CONCAT 등
6. **수치 분석**: 통계, 비율, 순위
7. **지리 데이터**: 위도/경도 기반 분석

이제 ChatGPT MCP를 통해 SQLite 데이터베이스에 직접 질의할 수 있습니다! 🚀

## 📋 빠른 시작 체크리스트

- [ ] `bird_collision_mcp.db` 파일 생성 확인
- [ ] Claude Desktop 설정 파일 수정
- [ ] Claude Desktop 재시작
- [ ] "조류 충돌 데이터베이스의 기본 통계를 알려주세요" 질의 테스트
- [ ] 복잡한 분석 쿼리 테스트