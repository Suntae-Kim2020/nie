-- MCP 테스트 쿼리: 철새vs텃새
-- 생성일: 2025-09-23 17:39:09


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
