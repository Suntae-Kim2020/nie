-- PostgreSQL MCP 테스트용 전체 쿼리 모음
-- 생성일: 2025-09-23 17:39:09

-- ============================================
-- 기본 통계
-- ============================================

-- 전체 통계 조회
SELECT 
    COUNT(*) as 총_사고건수,
    COUNT(DISTINCT korean_common_name) as 조류종_수,
    COUNT(DISTINCT province) as 시도_수,
    SUM(individual_count) as 총_개체수
FROM bird_collision_incidents;


-- ============================================
-- 위험 조류 TOP10
-- ============================================

-- 가장 위험한 조류 종 TOP 10
SELECT 
    korean_common_name as 조류종,
    COUNT(*) as 사고건수,
    SUM(individual_count) as 총_개체수,
    migratory_type as 철새유형,
    ROUND(AVG(individual_count), 2) as 평균_개체수
FROM bird_collision_incidents
GROUP BY korean_common_name, migratory_type
ORDER BY 사고건수 DESC
LIMIT 10;


-- ============================================
-- 지역별 위험도
-- ============================================

-- 지역별 사고 위험도 순위
SELECT 
    province as 시도,
    COUNT(*) as 사고건수,
    COUNT(DISTINCT korean_common_name) as 조류종_다양성,
    COUNT(DISTINCT facility_type) as 시설물_유형수,
    ROUND(calculate_facility_risk_score('방음벽'), 2) as 방음벽_위험도,
    array_agg(DISTINCT korean_common_name ORDER BY korean_common_name) as 주요_조류종
FROM bird_collision_incidents
GROUP BY province
ORDER BY 사고건수 DESC;


-- ============================================
-- 시설물별 분석
-- ============================================

-- 시설물별 상세 분석
SELECT 
    facility_type as 시설물유형,
    COUNT(*) as 사고건수,
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM bird_collision_incidents)), 2) as 비율_퍼센트,
    COUNT(DISTINCT korean_common_name) as 영향받은_조류종수,
    AVG(individual_count) as 평균_개체수,
    SUM(CASE WHEN bird_saver_installed THEN 1 ELSE 0 END) as 버드세이버_설치건수
FROM bird_collision_incidents
GROUP BY facility_type
ORDER BY 사고건수 DESC;


-- ============================================
-- 계절별 패턴
-- ============================================

-- 계절별 사고 패턴 분석
SELECT * FROM get_seasonal_analysis();


-- ============================================
-- 월별 트렌드
-- ============================================

-- 월별 사고 트렌드
SELECT 
    EXTRACT(MONTH FROM observation_date) as 월,
    COUNT(*) as 사고건수,
    COUNT(DISTINCT korean_common_name) as 조류종수,
    array_agg(DISTINCT korean_common_name ORDER BY korean_common_name) as 주요_종들
FROM bird_collision_incidents
GROUP BY EXTRACT(MONTH FROM observation_date)
ORDER BY 월;


-- ============================================
-- 버드세이버 효과
-- ============================================

-- 버드세이버 설치 효과 분석
SELECT 
    bird_saver_installed as 버드세이버_설치여부,
    COUNT(*) as 사고건수,
    AVG(individual_count) as 평균_개체수,
    COUNT(DISTINCT korean_common_name) as 영향받은_종수
FROM bird_collision_incidents
WHERE bird_saver_installed IS NOT NULL
GROUP BY bird_saver_installed;


-- ============================================
-- 핫스팟 분석
-- ============================================

-- 지역별 핫스팟 분석 (PostGIS 활용)
SELECT 
    province as 시도,
    total_incidents as 총_사고건수,
    ST_AsText(center_point) as 중심좌표,
    array_length(species_list, 1) as 조류종_수
FROM v_regional_hotspots
ORDER BY total_incidents DESC;


-- ============================================
-- 철새VS텃새
-- ============================================

-- 철새 vs 텃새 충돌 패턴 비교
SELECT 
    migratory_type as 철새유형,
    COUNT(*) as 사고건수,
    COUNT(DISTINCT korean_common_name) as 종_다양성,
    COUNT(DISTINCT province) as 영향지역수,
    AVG(individual_count) as 평균_개체수
FROM bird_collision_incidents
WHERE migratory_type IS NOT NULL
GROUP BY migratory_type
ORDER BY 사고건수 DESC;


