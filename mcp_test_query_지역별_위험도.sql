-- MCP 테스트 쿼리: 지역별_위험도
-- 생성일: 2025-09-23 17:39:09


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
