-- MCP 테스트 쿼리: 월별_트렌드
-- 생성일: 2025-09-23 17:39:09


-- 월별 사고 트렌드
SELECT 
    EXTRACT(MONTH FROM observation_date) as 월,
    COUNT(*) as 사고건수,
    COUNT(DISTINCT korean_common_name) as 조류종수,
    array_agg(DISTINCT korean_common_name ORDER BY korean_common_name) as 주요_종들
FROM bird_collision_incidents
GROUP BY EXTRACT(MONTH FROM observation_date)
ORDER BY 월;
