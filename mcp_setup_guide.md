# 🐦 PostgreSQL MCP 테스트 가이드

조류 충돌 데이터를 PostgreSQL에 설정하고 ChatGPT MCP를 통해 질의하는 완전한 가이드입니다.

## 📋 필요한 파일들

생성된 파일들:
- `postgresql_mcp_setup.sql` - 데이터베이스 스키마 설정
- `insert_bird_collision_data.sql` - 조류 충돌 데이터 삽입 (8,598개 레코드)
- `docker-compose.yml` - Docker 환경 설정
- `mcp_test_all_queries.sql` - 테스트용 쿼리 모음
- 개별 쿼리 파일들 (`mcp_test_query_*.sql`)

## 🚀 설정 단계

### 1. Docker로 PostgreSQL 시작

```bash
# Docker Compose로 PostgreSQL + PostGIS 시작
docker-compose up -d

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs postgres
```

### 2. 데이터베이스 연결 확인

```bash
# PostgreSQL 컨테이너 접속
docker exec -it bird_collision_postgres psql -U postgres -d bird_collision_db

# 또는 로컬에서 연결
psql -h localhost -p 5432 -U postgres -d bird_collision_db
```

### 3. 데이터 확인

```sql
-- 기본 통계
SELECT COUNT(*) FROM bird_collision_incidents;

-- 테이블 구조 확인
\d bird_collision_incidents

-- 샘플 데이터 조회
SELECT * FROM bird_collision_incidents LIMIT 5;
```

## 🔧 MCP 서버 설정

### 연결 정보
- **Host**: localhost
- **Port**: 5432
- **Database**: bird_collision_db
- **Username**: postgres
- **Password**: password123

### MCP 서버 설정 예시 (claude_desktop_config.json)

```json
{
  "mcpServers": {
    "postgresql": {
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-postgres",
        "postgresql://postgres:password123@localhost:5432/bird_collision_db"
      ]
    }
  }
}
```

## 📊 테스트용 쿼리들

### 1. 기본 통계
```sql
SELECT 
    COUNT(*) as 총_사고건수,
    COUNT(DISTINCT korean_common_name) as 조류종_수,
    COUNT(DISTINCT province) as 시도_수,
    SUM(individual_count) as 총_개체수
FROM bird_collision_incidents;
```

### 2. 위험 조류 TOP 10
```sql
SELECT 
    korean_common_name as 조류종,
    COUNT(*) as 사고건수,
    migratory_type as 철새유형
FROM bird_collision_incidents
GROUP BY korean_common_name, migratory_type
ORDER BY 사고건수 DESC
LIMIT 10;
```

### 3. 지역별 위험도
```sql
SELECT 
    province as 시도,
    COUNT(*) as 사고건수,
    COUNT(DISTINCT korean_common_name) as 조류종_다양성
FROM bird_collision_incidents
GROUP BY province
ORDER BY 사고건수 DESC;
```

### 4. 시설물별 분석
```sql
SELECT 
    facility_type as 시설물유형,
    COUNT(*) as 사고건수,
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM bird_collision_incidents)), 2) as 비율
FROM bird_collision_incidents
GROUP BY facility_type
ORDER BY 사고건수 DESC;
```

## 🧪 ChatGPT MCP 테스트 예시

ChatGPT에서 다음과 같이 질의할 수 있습니다:

### 기본 질의들
1. "조류 충돌 사고가 가장 많이 발생하는 조류 종은?"
2. "방음벽에서 발생하는 사고의 지역별 분포는?"
3. "계절별로 조류 충돌 패턴을 분석해줘"
4. "버드세이버 설치 효과는 어떻게 되나?"
5. "텃새와 철새 중 어느 쪽이 더 위험한가?"

### 복합 분석 질의들
1. "각 지역별로 가장 위험한 조류 종과 시설물 조합을 찾아줘"
2. "월별 사고 추이를 보고 조류 이동시기와 연관성을 분석해줘"
3. "지리적 위치를 기반으로 사고 핫스팟을 클러스터링해줘"
4. "시설물 유형별 위험도 점수를 계산하고 순위를 매겨줘"

### 고급 분석 질의들
1. "PostGIS를 활용해서 반경 5km 내 사고 클러스터를 찾아줘"
2. "조류 종별 선호하는 시설물과 계절적 패턴을 교차 분석해줘"
3. "기후 데이터와 연계해서 날씨가 조류 충돌에 미치는 영향을 분석해줘"

## 🔍 고급 기능

### 1. 사용자 정의 함수 활용
```sql
-- 시설물별 위험도 점수 계산
SELECT facility_type, calculate_facility_risk_score(facility_type) 
FROM (SELECT DISTINCT facility_type FROM bird_collision_incidents) f;

-- 계절별 분석 함수 사용
SELECT * FROM get_seasonal_analysis();
```

### 2. 공간 분석 (PostGIS)
```sql
-- 지역별 핫스팟 분석
SELECT * FROM v_regional_hotspots;

-- 반경 내 클러스터 분석
SELECT province, COUNT(*) as cluster_size,
       ST_AsText(ST_Centroid(ST_Collect(location))) as center
FROM bird_collision_incidents 
WHERE location IS NOT NULL
GROUP BY province;
```

### 3. 시계열 분석
```sql
-- 월별 트렌드 분석
SELECT * FROM v_monthly_statistics
ORDER BY year, month;
```

## 🛠️ 트러블슈팅

### Docker 관련 문제
```bash
# 컨테이너 재시작
docker-compose restart

# 볼륨 초기화 (데이터 삭제됨)
docker-compose down -v
docker-compose up -d

# 로그 확인
docker-compose logs -f postgres
```

### 연결 문제
```bash
# 포트 확인
lsof -i :5432

# PostgreSQL 상태 확인
docker exec bird_collision_postgres pg_isready -U postgres
```

### 데이터 문제
```sql
-- 데이터 재삽입
TRUNCATE TABLE bird_collision_incidents RESTART IDENTITY CASCADE;
-- 그 후 insert_bird_collision_data.sql 재실행
```

## 📈 성능 최적화

### 인덱스 추가
```sql
-- 자주 사용하는 조합에 대한 복합 인덱스
CREATE INDEX idx_province_facility ON bird_collision_incidents(province, facility_type);
CREATE INDEX idx_date_species ON bird_collision_incidents(observation_date, korean_common_name);
```

### 통계 업데이트
```sql
-- 쿼리 성능을 위한 통계 업데이트
ANALYZE bird_collision_incidents;
```

## 🎯 MCP 테스트 목표

1. **기본 CRUD 작업** - 데이터 조회, 삽입, 업데이트, 삭제
2. **복합 쿼리** - JOIN, GROUP BY, 집계 함수 사용
3. **공간 분석** - PostGIS 기능 활용
4. **시계열 분석** - 날짜/시간 기반 분석
5. **사용자 정의 함수** - PostgreSQL 함수 호출
6. **뷰 활용** - 미리 정의된 뷰 사용
7. **실시간 분석** - 대화형 데이터 탐색

이제 모든 준비가 완료되었습니다. Docker로 PostgreSQL을 시작하고 ChatGPT MCP를 통해 데이터베이스에 직접 질의할 수 있습니다! 🚀