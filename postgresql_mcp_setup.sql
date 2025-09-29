-- PostgreSQL MCP 테스트를 위한 조류 충돌 데이터베이스 설정
-- 사용법: PostgreSQL이 설치된 환경에서 실행

-- 1. 데이터베이스 생성
CREATE DATABASE bird_collision_db
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'ko_KR.UTF-8'
    LC_CTYPE = 'ko_KR.UTF-8'
    TEMPLATE = template0;

-- 데이터베이스 연결
\c bird_collision_db;

-- 2. 확장 설치 (지리정보 처리용)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- 3. 메인 테이블 생성
CREATE TABLE bird_collision_incidents (
    id SERIAL PRIMARY KEY,
    observation_number VARCHAR(50),
    survey_year INTEGER,
    observation_date DATE,
    registration_date DATE,
    korean_common_name VARCHAR(100) NOT NULL,
    migratory_type VARCHAR(20),
    habitat_type VARCHAR(50),
    scientific_name VARCHAR(200),
    english_name VARCHAR(200),
    taxonomy_kingdom VARCHAR(50),
    taxonomy_phylum VARCHAR(50),
    taxonomy_class VARCHAR(50),
    taxonomy_order VARCHAR(50),
    taxonomy_family VARCHAR(50),
    taxonomy_genus VARCHAR(100),
    taxonomy_species VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    individual_count INTEGER DEFAULT 1,
    facility_type VARCHAR(50),
    bird_saver_installed BOOLEAN,
    province VARCHAR(50),
    location GEOMETRY(POINT, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 인덱스 생성 (성능 최적화)
CREATE INDEX idx_bird_collision_date ON bird_collision_incidents(observation_date);
CREATE INDEX idx_bird_collision_province ON bird_collision_incidents(province);
CREATE INDEX idx_bird_collision_species ON bird_collision_incidents(korean_common_name);
CREATE INDEX idx_bird_collision_facility ON bird_collision_incidents(facility_type);
CREATE INDEX idx_bird_collision_migratory ON bird_collision_incidents(migratory_type);
CREATE INDEX idx_bird_collision_location ON bird_collision_incidents USING GIST(location);

-- 5. 통계 뷰 생성
CREATE VIEW v_collision_statistics AS
SELECT 
    province,
    facility_type,
    korean_common_name,
    migratory_type,
    COUNT(*) as incident_count,
    SUM(individual_count) as total_individuals,
    AVG(individual_count) as avg_individuals_per_incident,
    MIN(observation_date) as first_incident,
    MAX(observation_date) as latest_incident
FROM bird_collision_incidents
GROUP BY province, facility_type, korean_common_name, migratory_type;

-- 6. 월별 통계 뷰
CREATE VIEW v_monthly_statistics AS
SELECT 
    EXTRACT(YEAR FROM observation_date) as year,
    EXTRACT(MONTH FROM observation_date) as month,
    province,
    facility_type,
    COUNT(*) as incident_count,
    SUM(individual_count) as total_individuals
FROM bird_collision_incidents
GROUP BY EXTRACT(YEAR FROM observation_date), EXTRACT(MONTH FROM observation_date), province, facility_type
ORDER BY year, month, province;

-- 7. 지역별 핫스팟 뷰 (PostGIS 기능 활용)
CREATE VIEW v_regional_hotspots AS
SELECT 
    province,
    COUNT(*) as total_incidents,
    ST_Centroid(ST_Collect(location)) as center_point,
    ST_ConvexHull(ST_Collect(location)) as affected_area,
    array_agg(DISTINCT korean_common_name ORDER BY korean_common_name) as species_list
FROM bird_collision_incidents
WHERE location IS NOT NULL
GROUP BY province
HAVING COUNT(*) > 10
ORDER BY total_incidents DESC;

-- 8. 시설물별 위험도 함수
CREATE OR REPLACE FUNCTION calculate_facility_risk_score(facility VARCHAR)
RETURNS DECIMAL AS $$
DECLARE
    incident_count INTEGER;
    species_diversity INTEGER;
    avg_individuals DECIMAL;
    risk_score DECIMAL;
BEGIN
    SELECT 
        COUNT(*),
        COUNT(DISTINCT korean_common_name),
        AVG(individual_count)
    INTO incident_count, species_diversity, avg_individuals
    FROM bird_collision_incidents
    WHERE facility_type = facility;
    
    -- 위험도 점수 계산 (사고수 * 2 + 종다양성 * 1.5 + 평균개체수)
    risk_score := incident_count * 2 + species_diversity * 1.5 + avg_individuals;
    
    RETURN risk_score;
END;
$$ LANGUAGE plpgsql;

-- 9. 계절별 분석 함수
CREATE OR REPLACE FUNCTION get_seasonal_analysis()
RETURNS TABLE(
    season TEXT,
    incident_count BIGINT,
    top_species TEXT,
    most_dangerous_facility TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH seasonal_data AS (
        SELECT 
            CASE 
                WHEN EXTRACT(MONTH FROM observation_date) IN (3,4,5) THEN '봄'
                WHEN EXTRACT(MONTH FROM observation_date) IN (6,7,8) THEN '여름'
                WHEN EXTRACT(MONTH FROM observation_date) IN (9,10,11) THEN '가을'
                ELSE '겨울'
            END as season_name,
            korean_common_name,
            facility_type,
            COUNT(*) as count
        FROM bird_collision_incidents
        GROUP BY season_name, korean_common_name, facility_type
    ),
    season_summary AS (
        SELECT 
            season_name,
            SUM(count) as total_incidents,
            (array_agg(korean_common_name ORDER BY count DESC))[1] as top_species,
            (array_agg(facility_type ORDER BY count DESC))[1] as top_facility
        FROM seasonal_data
        GROUP BY season_name
    )
    SELECT 
        season_name,
        total_incidents,
        top_species,
        top_facility
    FROM season_summary
    ORDER BY total_incidents DESC;
END;
$$ LANGUAGE plpgsql;

-- 10. 트리거 함수 (지리 정보 자동 설정)
CREATE OR REPLACE FUNCTION update_location_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.location := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    END IF;
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 생성
CREATE TRIGGER tr_update_location
    BEFORE INSERT OR UPDATE ON bird_collision_incidents
    FOR EACH ROW
    EXECUTE FUNCTION update_location_trigger();

-- 11. 샘플 쿼리들 (MCP 테스트용)
/*
-- 기본 통계
SELECT COUNT(*) as total_incidents, 
       COUNT(DISTINCT korean_common_name) as species_count,
       COUNT(DISTINCT province) as province_count
FROM bird_collision_incidents;

-- 상위 위험 종
SELECT korean_common_name, COUNT(*) as incidents, migratory_type
FROM bird_collision_incidents 
GROUP BY korean_common_name, migratory_type 
ORDER BY incidents DESC LIMIT 10;

-- 지역별 사고 현황
SELECT province, COUNT(*) as incidents, 
       COUNT(DISTINCT korean_common_name) as species_variety
FROM bird_collision_incidents 
GROUP BY province 
ORDER BY incidents DESC;

-- 시설물별 위험도 점수
SELECT facility_type, calculate_facility_risk_score(facility_type) as risk_score
FROM (SELECT DISTINCT facility_type FROM bird_collision_incidents) f
ORDER BY risk_score DESC;

-- 계절별 분석
SELECT * FROM get_seasonal_analysis();

-- 월별 트렌드
SELECT EXTRACT(MONTH FROM observation_date) as month,
       COUNT(*) as incidents,
       array_agg(DISTINCT korean_common_name) as species
FROM bird_collision_incidents 
GROUP BY EXTRACT(MONTH FROM observation_date)
ORDER BY month;

-- 지리적 분석 (반경 1km 내 클러스터)
SELECT province, COUNT(*) as cluster_size,
       ST_AsText(ST_Centroid(ST_Collect(location))) as cluster_center
FROM bird_collision_incidents 
WHERE location IS NOT NULL
GROUP BY province
HAVING COUNT(*) > 5;
*/

-- 12. 권한 설정
GRANT ALL PRIVILEGES ON DATABASE bird_collision_db TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO postgres;