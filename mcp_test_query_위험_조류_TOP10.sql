-- MCP 테스트 쿼리: 위험_조류_TOP10
-- 생성일: 2025-09-23 17:39:09


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
